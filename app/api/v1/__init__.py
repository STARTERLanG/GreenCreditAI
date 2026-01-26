from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.config import router as config_router
from app.api.v1.documents import router as documents_router

api_router = APIRouter()
api_router.include_router(chat_router, prefix="/chat", tags=["Chat"])
api_router.include_router(documents_router, prefix="/documents", tags=["Documents"])
api_router.include_router(config_router, prefix="/config", tags=["Config"])
api_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
