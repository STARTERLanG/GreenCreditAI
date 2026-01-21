from typing import List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import BaseMessage
from app.services.llm_factory import llm_factory
from app.schemas.chat import IntentType
from app.core.logging import logger

class RouterAgent:
    def __init__(self):
        self.llm = llm_factory.get_router_model()
        
        # 定义路由的 System Prompt (使用中文标签优化识别率)
        system_template = """你是一个专业的绿色信贷助手路由系统。
你的唯一任务是分析用户的最新输入，并结合对话历史将其归类为以下四类之一：

1. 闲聊: 
   - 问候、自我介绍、感谢。
   - 对对话历史的回顾（如“我刚才说了什么”、“总结一下我们的对话”）。
   - 对 AI 能力的询问（如“你能做什么”）。
   - 与信贷业务无关的通用话题。
   (示例: "你好", "回顾一下刚才的问题", "谢谢", "今天天气不错")

2. 政策查询: 询问绿色信贷相关的政策、标准、定义、法规、赤道原则，或者明确要求查询知识库/数据库。
   (示例: "光伏行业准入标准是什么", "什么是绿色信贷", "查询知识库中关于代码5175的信息")

3. 文档分析: 用户上传了新文件，或者请求对某份特定文件进行首次全面分析。
   (示例: "分析这份财报", "提取该文件的关键指标")

4. 补充信息: 用户在回答之前 AI 提出的疑问，或者在补充之前缺失的材料信息（如补充公司名、贷款金额、项目细节等）。
   (示例: "公司名是某某科技", "这笔钱是用来买风电设备的", "我刚才漏掉了，行业是造纸业")

请仅输出分类标签字符串（例如 "政策查询"），不要包含任何其他解释。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder(variable_name="chat_history"), # 注入历史
            ("human", "{input}"),
        ])

        # 改用纯文本输出，避免 Function Calling 解析失败
        self.chain = prompt | self.llm | StrOutputParser()

    async def route(self, user_input: str, chat_history: List[BaseMessage] = []) -> IntentType:
        """执行路由判断"""
        logger.info(f"Routing user input: {user_input[:50]}...")
        try:
            # 获取原始文本响应
            result = await self.chain.ainvoke({
                "input": user_input,
                "chat_history": chat_history
            })
            cleaned_result = result.strip()
            
            logger.info(f"Router raw output: {cleaned_result}")
            
            # 中文关键词匹配
            if "政策" in cleaned_result or "查询" in cleaned_result:
                return IntentType.POLICY_QUERY
            elif "补充" in cleaned_result:
                return IntentType.SUPPLEMENTARY_INFO
            elif "文档" in cleaned_result or "分析" in cleaned_result:
                return IntentType.DOCUMENT_ANALYSIS
            else:
                return IntentType.GENERAL_CHAT
                
        except Exception as e:
            logger.error(f"Routing failed: {e}, falling back to GENERAL_CHAT")
            return IntentType.GENERAL_CHAT

router_agent = RouterAgent()
