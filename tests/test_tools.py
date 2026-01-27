from unittest.mock import AsyncMock, patch

import pytest

# 注意：我们在这里 patch 导入的路径，而不是对象本身的方法
# 这样可以完全避开 Pydantic 的拦截


@pytest.mark.asyncio
async def test_rag_tool():
    """测试本地政策库检索 (Mocked)"""
    mock_res = "MOCK_RAG_RESULT"

    # 模拟一个具有 ainvoke 方法的对象
    mock_tool = AsyncMock()
    mock_tool.ainvoke.return_value = mock_res

    with patch("app.tools.rag_tool.search_green_policy", mock_tool):
        # 重新从模块获取被 patch 后的引用
        from app.tools.rag_tool import search_green_policy

        result = await search_green_policy.ainvoke("光伏发电")

        assert result == mock_res
        mock_tool.ainvoke.assert_called_once_with("光伏发电")


@pytest.mark.asyncio
async def test_web_search_tool():
    """测试联网搜索 (Mocked)"""
    mock_response = [{"url": "http://example.com", "content": "test content"}]

    # 直接 Patch 模块内部使用的原始工具变量
    with patch("app.tools.search_tool._raw_tavily_tool") as mock_tool_instance:
        mock_tool_instance.ainvoke = AsyncMock(return_value=mock_response)

        # 导入被测试的包装函数
        from app.tools.search_tool import web_search_tool

        result = await web_search_tool.ainvoke("test query")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].page_content == "test content"
        assert result[0].metadata["url"] == "http://example.com"
        assert "#:~:text=" in result[0].metadata["location"]["text_fragment"]
        mock_tool_instance.ainvoke.assert_called_once_with("test query")


@pytest.mark.asyncio
async def test_tyc_tool():
    """测试天眼查企业查询 (Mocked)"""
    mock_info = "MOCK_TYC_INFO"

    mock_tool = AsyncMock()
    mock_tool.ainvoke.return_value = mock_info

    with patch("app.tools.tyc_tool.search_enterprise_info", mock_tool):
        from app.tools.tyc_tool import search_enterprise_info

        result = await search_enterprise_info.ainvoke("测试公司")

        assert result == mock_info
        mock_tool.ainvoke.assert_called_once_with("测试公司")
