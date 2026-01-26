from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.api import deps
from app.models.user import User
from app.schemas.chat import ChatRequest, UpdateSessionRequest
from app.services.session_service import session_service
from app.services.workflow_service import workflow_service

router = APIRouter()


@router.get("/sessions")
async def get_chat_history(current_user: Annotated[User, Depends(deps.get_current_user)]):
    """获取所有会话列表"""
    return session_service.list_sessions(user_id=current_user.id)


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str, current_user: Annotated[User, Depends(deps.get_current_user)]):
    """获取指定会话的详细历史"""
    session_data = session_service.get_session(session_id, user_id=current_user.id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_data


@router.post("/config/sync")
async def sync_config(request: ChatRequest):
    """同步前端配置，用于预热工具或验证 MCP 连接"""
    from app.core.logging import logger

    logger.info(f"[Config] Syncing configuration for session: {request.session_id}")
    if request.mcp_servers:
        names = [s.name for s in request.mcp_servers]
        logger.info(f"[Config] Received {len(names)} MCP Servers: {names}")
        # TODO: Initialize/Test MCP connections here

    if request.custom_tools:
        names = [t.name for t in request.custom_tools]
        logger.info(f"[Config] Received {len(names)} Custom Tools: {names}")

    return {"status": "synced", "mcp_count": len(request.mcp_servers), "tool_count": len(request.custom_tools)}


@router.post("/completions")
async def chat_completions(request: ChatRequest, current_user: Annotated[User, Depends(deps.get_current_user)]):
    """
    流式对话接口
    """
    return StreamingResponse(
        workflow_service.process_stream(request, user_id=current_user.id), media_type="text/event-stream"
    )


@router.delete("/sessions")
async def delete_all_sessions(current_user: Annotated[User, Depends(deps.get_current_user)]):
    """删除该用户的所有会话"""
    session_service.delete_all_sessions(user_id=current_user.id)
    return {"status": "success", "message": "All sessions deleted"}


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: Annotated[User, Depends(deps.get_current_user)]):
    """删除会话"""
    success = session_service.delete_session(session_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found or permission denied")
    return {"status": "success"}


@router.patch("/sessions/{session_id}")
async def update_session(session_id: str, request: UpdateSessionRequest):
    """更新会话标题"""
    session = session_service.update_title(session_id, request.title)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
