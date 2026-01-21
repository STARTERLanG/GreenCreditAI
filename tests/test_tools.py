import pytest

from app.core.config import settings
from app.tools.rag_tool import search_green_policy
from app.tools.search_tool import web_search_tool
from app.tools.tyc_tool import search_enterprise_info


@pytest.mark.asyncio
async def test_rag_tool():
    """测试本地政策库检索"""
    query = "光伏发电"
    result = await search_green_policy.ainvoke(query)

    assert isinstance(result, str)
    assert len(result) > 10
    # 本地库可能为空，所以只要不报错就行，或者根据实际情况断言


@pytest.mark.asyncio
async def test_web_search_tool():
    """测试联网搜索 (需要有效 API Key)"""
    if not settings.TAVILY_API_KEY:
        pytest.skip("Skipping web search test: TAVILY_API_KEY not set")

    query = "Green Credit Policy 2025"
    result = await web_search_tool.ainvoke(query)

    assert isinstance(result, list)
    assert len(result) > 0
    assert "url" in result[0]


@pytest.mark.asyncio
async def test_tyc_tool():
    """测试天眼查企业查询 (需要有效 API Token)"""
    if not settings.TIANYANCHA_TOKEN:
        pytest.skip("Skipping TYC test: TIANYANCHA_TOKEN not set")

    company_name = "北京百度网讯科技有限公司"
    result = await search_enterprise_info.ainvoke(company_name)

    assert isinstance(result, str)
    # 如果 Token 有效，结果里应该包含企业基本信息
    # 如果 Token 失效，结果里应该包含 "查询天眼查失败"
    if "查询天眼查失败" in result:
        pytest.fail(f"TYC API Error: {result}")
    else:
        assert "北京百度网讯科技有限公司" in result
        assert "统一社会信用代码" in result
