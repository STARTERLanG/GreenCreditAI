from typing import List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
from app.services.llm_factory import llm_factory
from app.core.logging import logger

class AnalysisAgent:
    def __init__(self):
        self.llm = llm_factory.get_expert_model()
        
        system_template = """你是专业的信贷财务与ESG分析师。
用户上传了一份文件（财报、ESG报告等），内容如下：

=== 文件内容开始 ===
{file_content}
=== 文件内容结束 ===

请根据文件内容以及之前的对话历史回答用户的问题。
要求：
1. 数据准确，引用文件中的具体数值。
2. 分析深入，结合绿色信贷标准评估风险。
3. 如果文件中没有相关信息，请明确告知。
4. 使用 Markdown 格式输出。"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{query}")
        ])

    async def run(self, query: str, file_context: str, chat_history: List[BaseMessage] = []):
        """执行分析"""
        if not file_context:
            yield "【系统提示】您似乎还没有上传文件，或者文件解析失败。请先上传文件。"
            return

        logger.info(f"Analysis Agent running. Context length: {len(file_context)}")
        safe_context = file_context[:100000] 
        
        chain = self.prompt | self.llm
        async for chunk in chain.astream({
            "query": query, 
            "file_content": safe_context,
            "chat_history": chat_history
        }):
            if chunk.content:
                yield chunk.content

analysis_agent = AnalysisAgent()
