import json
from collections.abc import AsyncGenerator
from typing import Any

from langgraph.checkpoint.memory import MemorySaver
from sqlmodel import Session

from app.agents.summarizer import summarizer_agent
from app.core.db import engine
from app.core.logging import logger
from app.graph.definitions import create_base_graph
from app.models.file import FileParsingCache
from app.schemas.chat import ChatRequest
from app.services.document_service import UPLOAD_CACHE
from app.services.session_service import session_service


class WorkflowService:
    # ... (NODE_NAMES remain same)
    NODE_NAMES = {
        "router": "意图识别",
        "extractor": "信息提取",
        "auditor": "合规预审",
        "policy_enrichment": "政策分析",
        "chat": "生成回复",
    }

    def __init__(self):
        self._memory = MemorySaver()
        self._graph = create_base_graph().compile(checkpointer=self._memory)

    async def _get_file_content(self, file_hash: str) -> dict | None:
        """从缓存或数据库获取文件内容"""
        # 1. 查内存
        if file_hash in UPLOAD_CACHE:
            return UPLOAD_CACHE[file_hash]

        # 2. 查数据库
        with Session(engine) as session:
            file_record = session.get(FileParsingCache, file_hash)
            if file_record:
                data = {
                    "content": file_record.content,
                    "filename": file_record.filename,
                }
                # 回填缓存
                UPLOAD_CACHE[file_hash] = data
                return data
        return None

    async def process_stream(self, request: ChatRequest, user_id: str | None = None) -> AsyncGenerator[str, None]:
        user_input = request.message
        session_id = request.session_id
        file_hashes = request.file_hashes

        logger.info(f"--- New Request (Event Stream) | Session: {session_id} ---")

        # 1. 准备输入
        new_docs, file_names, attachments_data = [], [], []
        for h in file_hashes:
            file_info = await self._get_file_content(h)
            if file_info:
                content = file_info["content"].strip()
                new_docs.append(content)
                file_names.append(file_info["filename"])
                attachments_data.append({"hash": h, "name": file_info["filename"], "content": content})

        inputs = {
            "user_query": user_input,
            "uploaded_documents": new_docs,
            "session_id": session_id,
            "is_completed": False,
            "custom_tools": request.custom_tools,
            "user_id": user_id,
        }

        # 0. 检查是否需要生成标题 (Fix: Check BEFORE appending user message)
        should_generate_title = False
        if session_id:
            session = session_service.get_session(session_id)
            # 如果 session 不存在(首条消息) 或 虽存在但历史为空(异常情况)且标题未改
            if not session:
                should_generate_title = True
            elif session["title"] == "新对话":
                # 只有当历史记录为空时才生成（避免多轮对话重复生成）
                history = session.get("history", [])
                if not history or len(history) == 0:
                    should_generate_title = True

        if session_id:
            session_service.append_message(
                session_id, "user", user_input, attachments=attachments_data or None, user_id=user_id
            )

        full_ai_response = ""
        thought_logs = []  # 仅用于持久化存储，不用于流式传输

        logger.info(
            f"[Workflow] Processing Request | Session: {session_id} | Input: {user_input[:50]}... | Docs: {len(new_docs)}"
        )

        if request.mcp_servers:
            logger.info(f"[Workflow] Received {len(request.mcp_servers)} MCP Servers configuration.")
            for srv in request.mcp_servers:
                logger.info(f"  - MCP Server: {srv.name} ({srv.type}) -> {srv.command}")

        # 发送初始状态
        yield self._pack_event("status_update", {"text": "系统已接收请求，准备开始处理..."})

        # 2. 基于 astream_events 的核心循环
        try:
            # version="v2" 是 LangChain 1.0+ 标准事件流
            async for event in self._graph.astream_events(
                inputs, config={"configurable": {"thread_id": session_id}}, version="v2"
            ):
                kind = event["event"]
                node_name = event.get("metadata", {}).get("langgraph_node", "")

                # --- A. 处理 LLM 流式输出 (Token) ---
                if kind == "on_chat_model_stream":
                    # 核心过滤逻辑：只允许特定的节点向用户说话
                    # Auditor, Router, Extractor 的输出是 JSON/决策，绝对不能泄露
                    if node_name in ["auditor", "router", "extractor"]:
                        continue

                    chunk = event["data"]["chunk"]

                    # 1. 忽略参数构建过程
                    if chunk.tool_call_chunks:
                        continue

                    content = chunk.content
                    if content:
                        # 2. 区分 Reasoning (CoT) 和 Answer
                        # 适配 DeepSeek R1 / OpenAI o1 或者通过节点名称判断
                        is_reasoning = False
                        # 如果 chunk 有 content_type="reasoning" (LangChain 1.1+)
                        if hasattr(chunk, "content_type") and chunk.content_type == "reasoning":
                            is_reasoning = True

                        if is_reasoning:
                            yield self._pack_event("thought_delta", {"delta": content})
                        else:
                            full_ai_response += content
                            yield self._pack_event("answer_delta", {"delta": content})

                # --- B. 处理工具调用 (Tools) ---
                elif kind == "on_tool_start":
                    if not event["name"].startswith("_"):
                        log_entry = {
                            "id": event["run_id"],
                            "name": event["name"],
                            "input": event["data"].get("input"),
                            "status": "running",
                        }
                        thought_logs.append(log_entry)  # 记录用于历史
                        yield self._pack_event("tool_start", log_entry)

                elif kind == "on_tool_end":
                    if not event["name"].startswith("_"):
                        log_entry = {
                            "id": event["run_id"],
                            "name": event["name"],
                            "output": str(event["data"].get("output")),
                            "status": "completed",
                        }

                        # 更新历史记录中的状态
                        for log in thought_logs:
                            if isinstance(log, dict) and log.get("id") == log_entry["id"]:
                                log["output"] = log_entry["output"]
                                log["status"] = "completed"
                                break

                        yield self._pack_event("tool_end", log_entry)

                # --- C. 节点状态更新 (Node Change) ---
                elif kind == "on_chain_start":
                    if node_name and event["name"] == node_name:
                        display_name = self.NODE_NAMES.get(node_name, node_name)
                        msg = f"正在执行步骤: {display_name}..."
                        yield self._pack_event("status_update", {"text": msg})
                        logger.info(f"[Workflow] Node Start: {node_name}")
                        thought_logs.append(msg)

                elif kind == "on_custom_event":
                    # 支持业务自定义事件
                    yield self._pack_event("status_update", event["data"])

        except Exception as e:
            logger.exception(f"Workflow Error: {e}")
            yield self._pack_event("error", f"处理过程中发生错误: {str(e)}")

        # 3. 持久化与收尾
        if session_id and full_ai_response:
            # 序列化 thought_logs
            serializable_logs = []
            for log in thought_logs:
                if isinstance(log, dict):
                    serializable_logs.append(json.dumps(log, default=str, ensure_ascii=False))
                else:
                    serializable_logs.append(str(log))

            session_service.append_message(
                session_id, "assistant", full_ai_response, thought_process=serializable_logs, user_id=user_id
            )

        if should_generate_title and session_id:
            try:
                context = f"文件名: {', '.join(file_names)}" if file_names else ""
                new_title = await summarizer_agent.generate_title(user_input, context=context)
                session_service.update_title(session_id, new_title)
            except Exception:
                pass

        logger.info(f"[Workflow] Request Completed | Session: {session_id} | Generated: {len(full_ai_response)} chars")
        yield self._pack_event("done", "")

    def _pack_event(self, event_type: str, payload: Any) -> str:
        def clean_obj(obj):
            if isinstance(obj, list):
                return [clean_obj(item) for item in obj]
            if isinstance(obj, dict):
                return {k: clean_obj(v) for k, v in obj.items()}
            if hasattr(obj, "to_json"):
                return obj.to_json()
            if hasattr(obj, "content"):
                return str(obj.content)
            return str(obj) if not isinstance(obj, (str, int, float, bool, type(None))) else obj

        # 针对 text delta 做清洗，防止工具标签泄露
        if event_type == "answer_delta" and isinstance(payload, dict) and "delta" in payload:
            import re

            # 移除 <function=...> ... </function> 或者是 <function=...> 单标签
            # 以及 <parameter=...>
            text = payload["delta"]
            # 简单清洗：如果包含 <function= 则尝试过滤，但在流式中很难完美过滤跨 chunk 的标签。
            # 这里做一个简单的仅针对 chunk 内部的关键词屏蔽，或者更好的方法是在前端不渲染。
            # 由于流式截断问题，后端正则很难完美。
            # 但 Qwen 的 leakage 通常是一个完整的 chunk。
            if "<function=" in text or "<parameter=" in text:
                # 这种情况下通常是模型抽风了，把 tool call 当文本输出了。
                # 我们选择直接丢弃包含这些 tag 的 chunk，或者 try replace。
                text = re.sub(r"<function=[^>]+>", "", text)
                text = re.sub(r"<parameter=[^>]+>", "", text)
                payload["delta"] = text

        data = {"event": event_type, "payload": clean_obj(payload)}
        try:
            json_str = json.dumps(data, ensure_ascii=False, default=str)
            return f"data: {json_str}\n\n"
        except Exception as e:
            logger.error(f"JSON Pack Error: {e}")
            return 'data: { "event": "error", "payload": "数据序列化失败" }\n\n'


workflow_service = WorkflowService()
