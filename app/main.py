from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1 import api_router
from app.core.config import settings
from app.core.db import init_db
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时的逻辑
    logger.info(f"Starting {settings.APP_ENV} environment...")

    try:
        init_db()  # 初始化业务数据库表
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed (likely locked): {e}")
        # 不抛出异常，允许应用启动

    yield
    # 关闭时的逻辑
    logger.info("Shutting down...")


app = FastAPI(
    title="GreenCredit AI",
    description="面向信贷经理的绿色信贷智能助手",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG,
)

# 注册路由
app.include_router(api_router, prefix="/api/v1")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 模板配置
templates = Jinja2Templates(directory="app/templates")


@app.get("/")
async def read_root(request: Request):
    """主页入口"""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/login")
async def login_page(request: Request):
    """登录页"""
    return templates.TemplateResponse(request=request, name="login.html")


if __name__ == "__main__":
    import uvicorn

    # 禁用 reload，避免 Windows 下的文件锁问题
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
