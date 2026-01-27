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
                content_str = file_record.content
                try:
                    docs_data = json.loads(content_str)
                    if isinstance(docs_data, list):
                        # 构建带结构化标记的文本，帮助 LLM 溯源
                        formatted_parts = []
                        for doc in docs_data:
                            metadata = doc.get("metadata", {})
                            page_content = doc.get("page_content", "")

                            # 根据类型添加标记
                            if "page" in metadata:
                                marker = f"[Page {metadata['page']}]"
                            elif "sheet" in metadata and "row" in metadata:
                                marker = f"[Sheet: {metadata['sheet']}, Row: {metadata['row']}]"
                            elif "slide" in metadata:
                                marker = f"[Slide {metadata['slide']}]"
                            elif "paragraph_index" in metadata:
                                marker = f"[Para {metadata['paragraph_index']}]"
                            else:
                                marker = ""

                            formatted_parts.append(f"{marker}\n{page_content}")

                        parsed_content = "\n\n".join(formatted_parts)
                    else:
                        parsed_content = str(docs_data)
                except (json.JSONDecodeError, TypeError):
                    parsed_content = content_str

                data = {
                    "content": parsed_content,
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

        # 1. 准备输入 (增加进度反馈)
        yield self._pack_event("status_update", {"text": "正在检索并准备文档上下文..."})

        new_docs, file_names, attachments_data = [], [], []
        for i, h in enumerate(file_hashes, 1):
            yield self._pack_event("status_update", {"text": f"正在读取文档 ({i}/{len(file_hashes)})..."})
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

        # 0. 检查是否需要生成标题
        should_generate_title = False
        if session_id:
            session = session_service.get_session(session_id)
            if not session or session["title"] == "新对话":
                history = session.get("history", []) if session else []
                if not history or len(history) == 0:
                    should_generate_title = True

        if session_id:
            session_service.append_message(
                session_id, "user", user_input, attachments=attachments_data or None, user_id=user_id
            )

        full_ai_response = ""
        full_thought_process = ""
        thought_logs = []

        # 2. 基于 astream_events 的核心循环
        try:
            async for event in self._graph.astream_events(
                inputs, config={"configurable": {"thread_id": session_id}}, version="v2"
            ):
                kind = event["event"]
                node_name = event.get("metadata", {}).get("langgraph_node", "")

                # --- A. 处理 LLM 输出流 (Token) ---
                if kind == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if chunk.tool_call_chunks:
                        continue

                    content = chunk.content
                    if not content:
                        continue

                    # 核心判定逻辑：思维链 (CoT) vs 正文回答
                    # 1. 显性判定：模型明确标记为推理内容 (如 DeepSeek R1)
                    is_explicit_reasoning = hasattr(chunk, "content_type") and chunk.content_type == "reasoning"

                    # 2. 隐性判定：非最终对话节点 (router, extractor, auditor, policy_enrichment) 产生的文本
                    # 在这些节点中，LLM 的输出通常是决策逻辑或核查过程，属于“思考”范畴
                    is_node_internal_thinking = node_name in ["auditor", "router", "extractor", "policy_enrichment"]

                    if is_explicit_reasoning or is_node_internal_thinking:
                        # 启发式过滤：如果内容看起来像结构化 JSON 块，则不作为思维链增量发送
                        # 场景：Extractor 产生 PROJECT_AUDIT JSON 时，由 status_update 提示进度而非展示源码
                        stripped_content = content.strip()
                        if stripped_content.startswith(("{", "[", "```json", "PROJECT_")):
                            pass  # 属于技术输出，仅累加到 full_thought_process 用于持久化，不 yield
                        else:
                            full_thought_process += content
                            yield self._pack_event("thought_delta", {"delta": content})
                    else:
                        # 只有 chat 节点的非推理内容才被视为最终回答
                        full_ai_response += content
                        yield self._pack_event("answer_delta", {"delta": content})

                # --- B. 工具执行状态 (Tool Execution) ---
                elif kind == "on_tool_start":
                    if not event["name"].startswith("_"):
                        log_entry = {
                            "id": event["run_id"],
                            "name": event["name"],
                            "input": event["data"].get("input"),
                            "status": "running",
                        }
                        thought_logs.append(log_entry)
                        yield self._pack_event("tool_start", log_entry)

                elif kind == "on_tool_end":
                    if not event["name"].startswith("_"):
                        log_entry = {
                            "id": event["run_id"],
                            "name": event["name"],
                            "output": str(event["data"].get("output")),
                            "status": "completed",
                        }
                        for log in thought_logs:
                            if isinstance(log, dict) and log.get("id") == log_entry["id"]:
                                log["output"] = log_entry["output"]
                                log["status"] = "completed"
                                break
                        yield self._pack_event("tool_end", log_entry)

                # --- C. 状态与自定义事件 ---
                elif kind == "on_chain_start":
                    if node_name and event["name"] == node_name:
                        display_name = self.NODE_NAMES.get(node_name, node_name)
                        yield self._pack_event("status_update", {"text": f"智能体正在：{display_name}..."})

                elif kind == "on_custom_event":
                    yield self._pack_event("status_update", event["data"])

        except Exception as e:
            logger.exception(f"Workflow Error: {e}")
            yield self._pack_event("error", f"处理过程中发生错误: {str(e)}")

        # 3. 持久化
        if session_id and full_ai_response:
            import re

            full_ai_response = re.sub(r"<function=[^>]+>", "", full_ai_response)
            full_ai_response = re.sub(r"<parameter=[^>]+>", "", full_ai_response)
            full_ai_response = full_ai_response.strip()

            serializable_logs = [
                json.dumps(log, default=str, ensure_ascii=False) if isinstance(log, dict) else str(log)
                for log in thought_logs
            ]
            if full_thought_process:
                serializable_logs.insert(0, f"Thinking: {full_thought_process}")

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

        yield self._pack_event("done", "")

    def _pack_event(self, event_type: str, payload: Any) -> str:
        """根据文协议进行增量打包"""

        def clean_obj(obj):
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            if isinstance(obj, list):
                return [clean_obj(item) for item in obj]
            if isinstance(obj, dict):
                return {k: clean_obj(v) for k, v in obj.items()}
            if hasattr(obj, "to_json"):
                return obj.to_json()
            if hasattr(obj, "dict"):
                return obj.dict()
            return str(obj)

        if event_type == "answer_delta" and "delta" in payload:
            import re

            text = payload["delta"]
            # 严格过滤工具标签残余
            text = re.sub(r"<function=[^>]*>", "", text)
            text = re.sub(r"<parameter=[^>]*>", "", text)
            # 强化流式起始符拦截
            if text.strip() in ["<", "<f", "<fu", "<fun", "<func", "<funct", "<functi", "<function", "<function="]:
                text = ""
            payload["delta"] = text

        data = {"event": event_type, "payload": clean_obj(payload)}
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


workflow_service = WorkflowService()
