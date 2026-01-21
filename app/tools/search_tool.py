from langchain_tavily import TavilySearch

from app.core.config import settings

# 使用官方推荐的专用包
web_search_tool = TavilySearch(max_results=5, search_depth="advanced", tavily_api_key=settings.TAVILY_API_KEY)

web_search_tool.name = "web_search"
web_search_tool.description = "检索互联网上的最新实时信息。当需要了解企业最新新闻、政策变更、公示信息或背景调查时使用。"
