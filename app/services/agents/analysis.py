from langchain_core.prompts import ChatPromptTemplate
from app.services.llm_factory import llm_factory
from app.core.logging import logger

class AnalysisAgent:
    def __init__(self):
        # 分析任务通常涉及长文本，使用 qwen-max (支持 30k+ token)
        self.llm = llm_factory.get_expert_model()
        
        system_template = """你是专业的信贷财务与ESG分析师。
用户上传了一份文件（财报、ESG报告等），内容如下：

=== 文件内容开始 ===
{file_content}
=== 文件内容结束 ===

请根据文件内容回答用户的问题。
要求：
1. 数据准确，引用文件中的具体数值。
2. 分析深入，结合绿色信贷标准评估风险。
3. 如果文件中没有相关信息，请明确告知。
4. 使用 Markdown 格式输出。

用户问题：{query}"""

        self.prompt = ChatPromptTemplate.from_template(system_template)

    async def run(self, query: str, file_context: str):
        """执行分析"""
        if not file_context:
            yield "【系统提示】您似乎还没有上传文件，或者文件解析失败。请先上传文件。"
            return

        logger.info(f"Analysis Agent running. Context length: {len(file_context)}")
        
        # 为了防止 Token 溢出，简单截断 (通义千问支持很长，但以防万一)
        # 生产环境应使用 Tokenizer 计算，这里简单按字符截断
        safe_context = file_context[:100000] 
        
        chain = self.prompt | self.llm
        async for chunk in chain.astream({"query": query, "file_content": safe_context}):
            if chunk.content:
                yield chunk.content

analysis_agent = AnalysisAgent()
