import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any

from langgraph.checkpoint.memory import MemorySaver

from app.agents.summarizer import summarizer_agent
from app.core.logging import logger
from app.schemas.chat import ChatRequest
from app.services.document_service import UPLOAD_CACHE
from app.services.graph_engine import create_base_graph
from app.services.session_service import session_service


class WorkflowEngine:
    NODE_TIPS = {
        "router": "正在分析您的意图...",
        "extractor": "正在提取企业与项目核心信息...",
        "enrichment": "材料已就绪，正在进行政策匹配与深度审核...",
        "auditor": "正在进行合规性预审...",
        "chat": "正在生成回复...",
    }

    def __init__(self):
        # 内存 Saver 是线程安全的单例
        self._memory = MemorySaver()
        # 预编译图
        self._graph = create_base_graph().compile(checkpointer=self._memory)

    async def process_stream(self, request: ChatRequest, graph_app: Any = None) -> AsyncGenerator[str, None]:
        user_input = request.message
        session_id = request.session_id
        file_hashes = request.file_hashes

        # 1. 准备初始状态
        new_docs = []
        file_names = []
        attachments_data = []

        for h in file_hashes:
            if h in UPLOAD_CACHE:
                file_info = UPLOAD_CACHE[h]
                content = file_info["content"].strip()
                new_docs.append(content)
                file_names.append(file_info["filename"])
                attachments_data.append({"hash": h, "name": file_info["filename"]})
                logger.info(f"Attached file loaded: {h} | Name: {file_info['filename']}")

        inputs = {
            "user_query": user_input,
            "uploaded_documents": new_docs,
            "session_id": session_id,
            "is_completed": False,
        }

        should_generate_title = False
        if session_id:
            session = session_service.get_session(session_id)
            if not session or (session.title == "新对话" and session.history == "[]"):
                should_generate_title = True

        if session_id:
            session_service.append_message(
                session_id,
                "user",
                user_input,
                attachments=attachments_data if attachments_data else None,
            )

        full_ai_response = ""

        try:
            # 使用内部维护的 graph (基于 MemorySaver)
            # 忽略传入的 graph_app 参数（如果有）
            config = {"configurable": {"thread_id": session_id}}
            yield self._pack_event("think", "系统已接收请求，准备开始处理...")

            async for event in self._graph.astream(inputs, config=config, stream_mode="updates"):
                for node_name, output in event.items():
                    tip = self.NODE_TIPS.get(node_name, "正在处理中...")
                    yield self._pack_event("think", tip)

                    if "final_report" in output and output["final_report"]:
                        content = output["final_report"]
                        if len(content) > 50:
                            chunk_size = 30
                            for i in range(0, len(content), chunk_size):
                                chunk = content[i : i + chunk_size]
                                full_ai_response += chunk
                                yield self._pack_event("token", chunk)
                                await asyncio.sleep(0.02)
                        else:
                            full_ai_response += content
                            yield self._pack_event("token", content)

            if session_id and full_ai_response:
                session_service.append_message(session_id, "assistant", full_ai_response)

            if should_generate_title and session_id:
                try:
                    context = f"文件名: {', '.join(file_names)}" if file_names else ""
                    new_title = await summarizer_agent.generate_title(user_input, context=context)
                    session_service.update_title(session_id, new_title)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Workflow Error: {e}")
            yield self._pack_event("error", str(e))

        yield self._pack_event("done", "")

    def _pack_event(self, event_type: str, payload: str) -> str:
        data = {"event": event_type, "payload": payload}
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


workflow_engine = WorkflowEngine()
