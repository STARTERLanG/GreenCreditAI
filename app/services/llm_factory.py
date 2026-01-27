import httpx
from langchain_openai import ChatOpenAI

from app.core.config import settings


class LLMFactory:
    def __init__(self):
        # 创建一个共享的异步客户端，显式禁用环境代理 (trust_env=False)
        # 增加默认超时时间，防止大型文档处理时连接断开
        self.http_client = httpx.AsyncClient(trust_env=False, timeout=60.0)

    def get_model(self, model_name: str, temperature: float = 0.1):
        """
        获取 LLM 实例 (使用 ChatOpenAI 客户端连接阿里云千问)
        Qwen 的 OpenAI 兼容接口地址: https://dashscope.aliyuncs.com/compatible-mode/v1
        """
        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            streaming=True,
            http_async_client=self.http_client,
            request_timeout=60.0,  # 显式设置 OpenAI 客户端超时
        )

    def get_router_model(self):
        return self.get_model(settings.MODEL_ROUTER_NAME, temperature=0.1)

    def get_expert_model(self):
        return self.get_model(settings.MODEL_EXPERT_NAME, temperature=0.3)

    def get_fast_model(self):
        return self.get_model(settings.MODEL_FAST_NAME, temperature=0.5)


llm_factory = LLMFactory()
