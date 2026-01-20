from app.services.graph_engine import graph_app
from app.services.session_service import session_service
from app.services.document_service import UPLOAD_CACHE
from app.agents.summarizer import summarizer_agent
from app.schemas.chat import ChatRequest
from app.core.logging import logger
import json
from typing import AsyncGenerator

class WorkflowEngine:
    # ... (NODE_TIPS 不变)
    NODE_TIPS = {
        "router": "正在分析您的意图...",
        "extractor": "正在提取企业与项目核心信息...",
        "enrichment": "材料已就绪，正在进行政策匹配与深度审核...",
        "auditor": "正在进行合规性预审...",
        "chat": "正在生成回复..."
    }

    async def process_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        # ... (内部逻辑直到 try 块末尾)
        user_input = request.message
        session_id = request.session_id
        file_hashes = request.file_hashes
        
        new_docs = []
        file_names = []
        for h in file_hashes:
            if h in UPLOAD_CACHE:
                file_info = UPLOAD_CACHE[h]
                content = file_info["content"].strip()
                new_docs.append(content)
                file_names.append(file_info["filename"])
                # 打印内容预览，帮助排查解析是否为空
                preview = content[:200].replace('\n', ' ')
                logger.info(f"Attached file loaded: {h} | Name: {file_info['filename']} | Content Length: {len(content)}")
                logger.info(f"Content Preview: [{preview}]")
            else:
                logger.warning(f"File hash {h} not found in cache.")
        
        inputs = {
            "user_query": user_input,
            "uploaded_documents": new_docs,
            "session_id": session_id,
            "is_completed": False
        }

        should_generate_title = False
        if session_id:
            session = session_service.get_session(session_id)
            if not session or (session.title == "新对话" and session.history == "[]"):
                should_generate_title = True

        if session_id:
            db_save_text = user_input
            if file_names:
                db_save_text = f"[附件: {', '.join(file_names)}]\n{user_input}"
            session_service.append_message(session_id, "user", db_save_text)

        full_ai_response = ""
        
        try:
            config = {"configurable": {"thread_id": session_id}}
            yield self._pack_event("think", "系统已接收请求，准备开始处理...")

            async for event in graph_app.astream(inputs, config=config, stream_mode="updates"):
                for node_name, output in event.items():
                    # 发送节点状态提示
                    tip = self.NODE_TIPS.get(node_name, "正在处理中...")
                    yield self._pack_event("think", tip)
                    
                    # 模拟处理延迟，让前端用户能看清进度变化
                    import asyncio
                    await asyncio.sleep(0.2)
                    
                    if "final_report" in output and output["final_report"]:
                        content = output["final_report"]
                        logger.info(f"[Node {node_name} Output]: {content[:200]}...") 
                        
                        if len(content) > 50:
                            chunk_size = 30
                            for i in range(0, len(content), chunk_size):
                                chunk = content[i : i + chunk_size]
                                full_ai_response += chunk
                                yield self._pack_event("token", chunk)
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
                except Exception as e:
                    logger.error(f"Failed to auto-generate title: {e}")

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            yield self._pack_event("error", f"处理过程中发生错误: {str(e)}")

        yield self._pack_event("done", "")

    def _pack_event(self, event_type: str, payload: str) -> str:
        data = {"event": event_type, "payload": payload}
        sse_string = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        return sse_string

workflow_engine = WorkflowEngine()
