from langchain_openai import ChatOpenAI

from app.core.config import settings


class LLMFactory:
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
        )

    def get_router_model(self):
        return self.get_model(settings.MODEL_ROUTER_NAME, temperature=0.1)

    def get_expert_model(self):
        return self.get_model(settings.MODEL_EXPERT_NAME, temperature=0.3)


llm_factory = LLMFactory()
