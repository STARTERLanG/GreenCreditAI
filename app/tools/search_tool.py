from urllib.parse import quote

from langchain_core.documents import Document
from langchain_core.tools import tool
from langchain_tavily import TavilySearch

from app.core.cache import tool_cache
from app.core.config import settings
from app.core.logging import logger

# 原始 Tavily 工具实例
_raw_tavily_tool = TavilySearch(max_results=5, tavily_api_key=settings.TAVILY_API_KEY)


def generate_text_fragment(text: str) -> str:
    """
    为给定的文本生成 Chrome Text Fragment 锚点 (#:~:text=start,end)
    """
    if not text:
        return ""

    words = text.split()
    if len(words) < 2:
        start = quote(text[:10])
        end = ""
    else:
        # 选取前 3 个词和最后 3 个词作为界定符
        start = quote(" ".join(words[:3]))
        end = quote(" ".join(words[-3:]))

    if end:
        return f"#:~:text={start},{end}"
    return f"#:~:text={start}"


@tool
@tool_cache
async def web_search_tool(query: str) -> list[Document]:
    """
    检索互联网上的最新实时信息。当需要了解企业最新新闻、政策变更、公示信息或背景调查时使用。
    """
    logger.info(f"[Tool:WebSearch] Starting search for query: '{query}'")
    try:
        # Tavily .ainvoke returns a list of dictionaries
        results = await _raw_tavily_tool.ainvoke(query)

        documents = []
        for i, res in enumerate(results, 1):
            content = res.get("content", "").strip()
            if not content:
                continue

            url = res.get("url", "")
            title = res.get("title") or url.split("/")[-1] or "Relevant Page"

            # 生成定位锚点
            fragment = generate_text_fragment(content[:200])  # 针对片段开头

            doc = Document(
                page_content=content,
                metadata={
                    "source_type": "web_search",
                    "url": url,
                    "title": title,
                    "snippet_index": i,
                    "location": {"rank": i, "text_fragment": fragment},
                },
            )
            documents.append(doc)

        logger.info(f"[Tool:WebSearch] Search completed. Found {len(documents)} high-fidelity sources.")
        return documents
    except Exception as e:
        logger.error(f"[Tool:WebSearch] Execution failed: {e}")
        # 返回一个包含错误信息的文档，以便 Agent 知道发生了什么
        return [Document(page_content=f"Search failed: {e}", metadata={"error": True})]
