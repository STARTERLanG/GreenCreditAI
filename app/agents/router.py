from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.core.logging import logger
from app.core.prompts import Prompts
from app.schemas.chat import IntentType
from app.services.llm_factory import llm_factory


class RouterAgent:
    def __init__(self):
        self.llm = llm_factory.get_router_model()
        self.parser = StrOutputParser()

    async def route(self, user_input: str, chat_history: list = None, config: RunnableConfig = None) -> IntentType:
        """根据用户输入和历史记录判断意图"""
        logger.info(f"Routing user input: {user_input[:50]}...")

        # 构建 Prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", Prompts.ROUTER_SYSTEM),
            ("human", "历史记录：{chat_history}\n当前输入：{input}")
        ])

        chain = prompt | self.llm | self.parser

        try:
            raw_intent = await chain.ainvoke(
                {"input": user_input, "chat_history": chat_history or []},
                config=config
            )
            # 清理输出并转换为 Enum
            intent_str = raw_intent.strip()
            logger.info(f"Router raw output: {intent_str}")
            return IntentType(intent_str)
        except Exception as e:
            logger.warning(
                f"Router failed to parse ({raw_intent if 'raw_intent' in locals() else 'N/A'}), defaulting to GENERAL_CHAT. Error: {e}"
            )
            return IntentType.GENERAL_CHAT


router_agent = RouterAgent()
