from typing import List
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
from app.services.llm_factory import llm_factory
from app.rag.vector_store import vector_service
from app.core.logging import logger

class PolicyAgent:
    def __init__(self):
        self.llm = llm_factory.get_expert_model()
        
        system_template = """你是绿色信贷领域的资深政策专家。
请结合提供的背景信息以及之前的对话历史回答用户的问题。

背景信息：
{context}

回答要求：
1. 逻辑清晰，条理分明。
2. 尽量引用背景信息中的具体条款或分类。
3. 如果背景信息中没有相关内容，请诚实告知，不要编造。
4. 使用 Markdown 格式输出。"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_template),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{query}")
        ])

    async def run(self, query: str, chat_history: List[BaseMessage] = []):
        """执行 RAG 流程"""
        # 1. 检索上下文 (基于用户当前问题)
        docs = vector_service.search(query, k=5)
        context = "\n---\n".join([doc.page_content for doc in docs])
        
        # 2. 调用大模型生成回答 (流式)
        logger.info(f"Policy Agent generating answer with context length: {len(context)}")
        
        chain = self.prompt | self.llm
        async for chunk in chain.astream({
            "context": context, 
            "query": query,
            "chat_history": chat_history
        }):
            if chunk.content:
                yield chunk.content

policy_agent = PolicyAgent()
