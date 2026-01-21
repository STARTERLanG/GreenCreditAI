from langchain_core.tools import tool
from app.rag.vector_store import vector_store

@tool

async def search_green_policy(query: str) -> str:

    """

    检索《绿色金融支持项目目录（2025年版）》。

    输入企业名称、经营范围或贷款用途，返回相关的政策条目和说明。

    """

    try:

        # 使用异步检索方法

        results = await vector_store.asearch(query, k=5)

        if not results:

            return "未找到相关政策条目。"

        

        context = "\n\n".join([f"条目: {doc.page_content}" for doc in results])

        return context

    except Exception as e:

        return f"检索失败: {str(e)}"
