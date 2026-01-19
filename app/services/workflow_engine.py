import json
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage, SystemMessage

from app.schemas.chat import ChatRequest, IntentType
from app.services.agents.router import router_agent
from app.services.agents.policy import policy_agent
from app.services.agents.analysis import analysis_agent
from app.services.agents.summarizer import summarizer_agent
from app.services.llm_factory import llm_factory
from app.services.document_service import UPLOAD_CACHE
from app.services.session_service import session_service
from app.core.logging import logger

class WorkflowEngine:
    async def process_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """
        处理对话请求并生成流式响应 (SSE Format)
        """
        user_input = request.message
        session_id = request.session_id
        
        # 0. 检查是否需要生成标题 (如果当前会话不存在或 title 为"新对话"且历史为空)
        should_generate_title = False
        if session_id:
            session = session_service.get_session(session_id)
            # 如果是新创建的session(None) 或者 刚创建还没改名
            if not session or (session.title == "新对话" and session.history == "[]"):
                should_generate_title = True

        # 1. 持久化用户消息
        if session_id:
            session_service.append_message(session_id, "user", user_input)

        # 全量收集 AI 回复用于存储
        full_ai_response = ""
        
        # ... (路由和生成逻辑保持不变)
        # 2. 路由阶段
        yield self._pack_event("think", "正在分析您的意图...")
        intent = await router_agent.route(user_input)
        
        # 3. 分发逻辑
        if intent == IntentType.GENERAL_CHAT:
            yield self._pack_event("think", "识别为：闲聊模式")
            async for token in self._handle_general_chat(user_input):
                full_ai_response += token
                yield self._pack_event("token", token)
                
        elif intent == IntentType.POLICY_QUERY:
            yield self._pack_event("think", "识别为：政策查询，正在检索政策库...")
            async for token in policy_agent.run(user_input):
                full_ai_response += token
                yield self._pack_event("token", token)
            
        elif intent == IntentType.DOCUMENT_ANALYSIS:
            yield self._pack_event("think", "识别为：文档分析，读取最近上传的文件...")
            latest_file = UPLOAD_CACHE.get("latest")
            file_content = latest_file["content"] if latest_file else ""
            filename = latest_file["filename"] if latest_file else "未找到文件"
            
            if file_content:
                yield self._pack_event("think", f"正在分析文件: {filename}")
                async for token in analysis_agent.run(user_input, file_content):
                    full_ai_response += token
                    yield self._pack_event("token", token)
            else:
                msg = "请先点击输入框左侧的图标上传一份文档（支持 PDF/Excel），然后再让我分析。"
                full_ai_response = msg
                yield self._pack_event("token", msg)
        
        # 4. 持久化 AI 回复
        if session_id and full_ai_response:
            session_service.append_message(session_id, "assistant", full_ai_response)

        # 5. 自动生成标题 (如果是首轮对话)
        if should_generate_title and session_id:
            try:
                # 结合用户输入生成标题
                new_title = await summarizer_agent.generate_title(user_input)
                session_service.update_title(session_id, new_title)
                # 通知前端刷新列表 (可选: 通过 SSE 发送一个特殊事件 update_title)
                # 这里暂时依赖前端在 done 之后的自动刷新
            except Exception as e:
                logger.error(f"Failed to auto-generate title: {e}")

        # 6. 结束
        yield self._pack_event("done", "")

    async def _handle_general_chat(self, query: str) -> AsyncGenerator[str, None]:
        """处理闲聊，使用小模型直接回复 (仅返回原始文本)"""
        llm = llm_factory.get_router_model()
        messages = [
            SystemMessage(content="你是一个乐于助人的绿色信贷助手。请用专业但亲切的口吻简短回答用户的日常问候。"),
            HumanMessage(content=query)
        ]
        
        async for chunk in llm.astream(messages):
            if chunk.content:
                yield chunk.content

    def _pack_event(self, event_type: str, payload: str) -> str:
        """封装 SSE 格式数据"""
        data = {
            "event": event_type,
            "payload": payload
        }
        # ensure_ascii=False 保证中文不乱码，方便调试
        sse_string = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        
        # 调试日志：打印即将发送的 SSE 数据 (截断以防刷屏)
        preview = sse_string.replace('\n', '\\n')[:100]
        logger.debug(f"[SSE Out] {preview}...")
        
        return sse_string

workflow_engine = WorkflowEngine()
