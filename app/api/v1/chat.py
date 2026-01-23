from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, UpdateSessionRequest
from app.services.session_service import session_service
from app.services.workflow_service import workflow_service

router = APIRouter()


@router.get("/sessions")
async def get_chat_history():
    """获取所有会话列表"""
    return session_service.list_sessions()


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str):
    """获取指定会话的详细历史"""
    session_data = session_service.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_data


@router.post("/completions")
async def chat_completions(request: ChatRequest):
    """
    流式对话接口
    """
    return StreamingResponse(workflow_service.process_stream(request), media_type="text/event-stream")


@router.delete("/sessions")
async def delete_all_sessions():
    """删除所有会话"""
    session_service.delete_all_sessions()
    return {"status": "success"}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话"""
    success = session_service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"status": "success"}


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    """更新会话标题"""
    session = session_service.update_title(session_id, request.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
