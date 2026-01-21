from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.core.db import engine
from app.models.session import ChatSession
from app.schemas.chat import ChatRequest, UpdateSessionRequest
from app.services.session_service import session_service
from app.services.workflow_engine import workflow_engine

router = APIRouter()


@router.get("/sessions")
async def list_sessions():
    """获取会话列表"""
    with Session(engine) as session:
        # 按更新时间倒序
        statement = select(ChatSession).order_by(ChatSession.updated_at.desc())
        results = session.exec(statement).all()

        return [{"id": s.id, "title": s.title, "updated_at": s.updated_at} for s in results]


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
        "history": json.loads(session_data.history),
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    with Session(engine) as session:
        chat_session = session.get(ChatSession, session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")
        session.delete(chat_session)
        session.commit()
    return {"status": "success"}


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, payload: UpdateSessionRequest):
    """重命名会话"""
    with Session(engine) as session:
        chat_session = session.get(ChatSession, session_id)
        if not chat_session:
            raise HTTPException(status_code=404, detail="Session not found")
        chat_session.title = payload.title
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)  # 刷新以获取最新状态
        # 在 session 作用域内提取需要的数据
        new_title = chat_session.title

    return {"status": "success", "title": new_title}


@router.post("/completions")
async def chat_completions(request: ChatRequest):
    """
    流式对话接口
    """
    return StreamingResponse(workflow_engine.process_stream(request), media_type="text/event-stream")
