import sys
from loguru import logger
from app.core.config import settings

def setup_logging():
    """配置 Loguru 日志"""
    # 移除默认 handler
    logger.remove()
    
    # 添加标准输出 handler
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )
    
    # 也可以添加文件日志记录
    logger.add(
        "logs/app.log",
        rotation="10 MB",
        retention="10 days",
        level="INFO",
        encoding="utf-8",
    )

setup_logging()
