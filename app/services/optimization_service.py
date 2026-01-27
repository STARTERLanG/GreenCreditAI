from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.logging import logger
from app.core.prompts import Prompts
from app.services.llm_factory import llm_factory


class OptimizationService:
    def __init__(self):
        # 使用配置好的 Fast Model (Qwen-Turbo)
        self.llm = llm_factory.get_fast_model()

    async def optimize_input(self, user_input: str) -> str:
        """
        优化用户输入，使其更加清晰明确
        """
        try:
            prompt = ChatPromptTemplate.from_template(Prompts.OPTIMIZER_SYSTEM)
            chain = prompt | self.llm | StrOutputParser()

            logger.info(f"Optimizing input: {user_input[:50]}...")
            optimized_text = await chain.ainvoke({"input": user_input})

            # Post-processing: remove common prefixes
            cleaned_text = optimized_text.strip()
            prefixes_to_remove = ["优化后的Prompt：", "Optimization Result:", "优化后的提示词：", "Optimized Query:"]
            for prefix in prefixes_to_remove:
                if cleaned_text.startswith(prefix):
                    cleaned_text = cleaned_text[len(prefix) :].strip()

            logger.info("Input optimization completed")

            return cleaned_text
        except Exception:
            logger.exception("Input optimization failed")
            # 降级策略：如果优化失败，返回原输入，避免阻断流程
            return user_input


optimization_service = OptimizationService()
