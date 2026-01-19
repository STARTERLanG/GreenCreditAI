from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.llm_factory import llm_factory
from app.schemas.chat import IntentType
from app.core.logging import logger

class RouterAgent:
    def __init__(self):
        self.llm = llm_factory.get_router_model()
        
        # 定义路由的 System Prompt (使用中文标签优化识别率)
        system_template = """你是一个专业的绿色信贷助手路由系统。
你的唯一任务是分析用户的输入，并将其归类为以下三类之一：

1. 闲聊: 问候、自我介绍、感谢、与金融业务无关的话题。
   (示例: "你好", "你是谁", "谢谢", "今天天气不错")

2. 政策查询: 询问绿色信贷相关的政策、标准、定义、法规、赤道原则，或者明确要求查询知识库/数据库。
   (示例: "光伏行业准入标准是什么", "什么是绿色信贷", "查询知识库中关于代码5175的信息", "知识库里有什么内容")

3. 文档分析: 请求分析特定的文件、财报、数据，或者上下文中明显涉及对已上传文件的处理。
   (示例: "分析这份财报", "提取文件中的营收数据", "这家公司有环境风险吗")

请仅输出分类标签字符串（例如 "政策查询"），不要包含任何其他解释。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            ("human", "{input}"),
        ])

        # 改用纯文本输出，避免 Function Calling 解析失败
        self.chain = prompt | self.llm | StrOutputParser()

    async def route(self, user_input: str) -> IntentType:
        """执行路由判断"""
        logger.info(f"Routing user input: {user_input[:50]}...")
        try:
            # 获取原始文本响应
            result = await self.chain.ainvoke({"input": user_input})
            cleaned_result = result.strip()
            
            logger.info(f"Router raw output: {cleaned_result}")
            
            # 中文关键词匹配
            if "政策" in cleaned_result or "查询" in cleaned_result:
                return IntentType.POLICY_QUERY
            elif "文档" in cleaned_result or "分析" in cleaned_result:
                return IntentType.DOCUMENT_ANALYSIS
            else:
                return IntentType.GENERAL_CHAT
                
        except Exception as e:
            logger.error(f"Routing failed: {e}, falling back to GENERAL_CHAT")
            return IntentType.GENERAL_CHAT

router_agent = RouterAgent()
