from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from app.schemas.chat import ChatRequest
from app.services.workflow_engine import workflow_engine
from app.services.session_service import session_service
from app.core.db import engine
from app.models.session import ChatSession

router = APIRouter()

@router.get("/sessions")
async def list_sessions():
    """获取会话列表 (仅返回非空会话或最近创建的)"""
    with Session(engine) as session:
        # 按更新时间倒序
        statement = select(ChatSession).order_by(ChatSession.updated_at.desc())
        results = session.exec(statement).all()
        # 简单过滤：实际生产中建议在 SQL 层过滤，这里在 Python 层处理
        valid_sessions = []
        for s in results:
            if s.history and s.history != "[]":
                valid_sessions.append({"id": s.id, "title": s.title, "updated_at": s.updated_at})
            # 保留最近一个即使为空的会话（方便调试）
            elif len(valid_sessions) == 0: 
                 valid_sessions.append({"id": s.id, "title": s.title, "updated_at": s.updated_at})
                 
        return valid_sessions

@router.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """获取单个会话的完整历史"""
    session_data = session_service.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    import json
    return {
        "id": session_data.id,
        "title": session_data.title,
        "history": json.loads(session_data.history)
    }

@router.post("/completions")
async def chat_completions(request: ChatRequest):
    """
    流式对话接口
    """
    return StreamingResponse(
        workflow_engine.process_stream(request),
        media_type="text/event-stream"
    )
