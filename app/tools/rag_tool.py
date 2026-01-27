from langchain_core.tools import tool

from app.core.logging import logger
from app.rag.vector_store import vector_store


@tool
async def search_green_policy(query: str) -> str:
    """
    检索《绿色金融支持项目目录（2025年版）》。
    输入企业名称、经营范围或贷款用途，返回相关的政策条目和说明。
    """
    logger.info(f"[Tool:RAG] Searching policy for query: '{query}'")
    try:
        # 使用异步检索方法
        results = await vector_store.asearch(query, k=5)

        if not results:
            logger.warning(f"[Tool:RAG] No policy found for: '{query}'")
            return "未找到相关政策条目。"

        formatted_results = []
        for i, doc in enumerate(results, 1):
            source = doc.metadata.get("filename") or doc.metadata.get("source") or "Unknown"
            page = doc.metadata.get("page") or doc.metadata.get("page_estimate") or doc.metadata.get("slide") or ""
            page_info = f", Page {page}" if page else ""

            content = f"[{i}] Source: {source}{page_info}\nContent: {doc.page_content}"
            formatted_results.append(content)

        context = "\n\n---\n\n".join(formatted_results)
        return context

    except Exception as e:
        logger.exception(f"[Tool:RAG] Search Error: {e}")
        return f"检索失败: {str(e)}"
