from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.core.logging import logger
from app.services.llm_factory import llm_factory


class SummarizerAgent:
    def __init__(self):
        # 使用小模型 qwen-turbo，速度快且便宜
        self.llm = llm_factory.get_router_model()

        system_template = """你是一个专业的对话标题生成器。
请根据用户的输入生成一个简短、精准的标题。
要求：
1. 长度控制在 4-10 个字以内。
2. 不要包含“用户问”、“关于”等冗余词汇。
3. 直接输出标题内容，不要有引号或其他修饰。

用户输入：{input}"""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_template),
            ]
        )

        self.chain = prompt | self.llm | StrOutputParser()

    async def generate_title(self, user_input: str, context: str = "") -> str:
        """生成会话标题"""
        try:
            # 组装更丰富的素材
            input_text = f"用户提问: {user_input}\n其他上下文: {context}"
            safe_input = input_text[:300]

            title = await self.chain.ainvoke({"input": safe_input})
            clean_title = title.strip().replace('"', "").replace("《", "").replace("》", "").replace(" ", "")
            logger.info(f"Generated title: {clean_title}")
            return clean_title
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return "新对话"


summarizer_agent = SummarizerAgent()
