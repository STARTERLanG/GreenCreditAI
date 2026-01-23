from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from app.core.cache import tool_cache
from app.core.config import settings
from app.core.logging import logger

# 原始 Tavily 工具实例
_raw_tavily_tool = TavilySearch(max_results=5, tavily_api_key=settings.TAVILY_API_KEY)


@tool
@tool_cache
async def web_search_tool(query: str) -> str:
    """
    检索互联网上的最新实时信息。当需要了解企业最新新闻、政策变更、公示信息或背景调查时使用。
    """
    logger.info(f"[Tool:WebSearch] Starting search for query: '{query}'")
    try:
        # 代理调用原始工具
        result = await _raw_tavily_tool.ainvoke(query)
        logger.info(f"[Tool:WebSearch] Search completed. Result length: {len(str(result))} chars")
        logger.debug(f"[Tool:WebSearch] Raw result: {str(result)[:500]}...")
        return result
    except Exception as e:
        logger.error(f"[Tool:WebSearch] Execution failed: {e}")
        return f"Search failed: {e}"
