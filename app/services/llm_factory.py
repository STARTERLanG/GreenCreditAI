from langchain_community.chat_models import ChatTongyi

from app.core.config import settings
from app.core.logging import logger


class LLMFactory:
    """LLM 客户端工厂类，管理大小模型的初始化"""

    @staticmethod
    def get_router_model() -> ChatTongyi:
        """获取 L1 路由模型 (小模型)"""
        logger.info(f"Initializing router model: {settings.MODEL_ROUTER_NAME}")
        return ChatTongyi(
            model_name=settings.MODEL_ROUTER_NAME,
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            streaming=True,
        )

    @staticmethod
    def get_expert_model() -> ChatTongyi:
        """获取 L2 专家模型 (大模型)"""
        logger.info(f"Initializing expert model: {settings.MODEL_EXPERT_NAME}")
        return ChatTongyi(
            model_name=settings.MODEL_EXPERT_NAME,
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            streaming=True,
        )


# 单例模式或工厂方法供外部调用
llm_factory = LLMFactory()
