import pytest
from langchain_core.messages import HumanMessage

from app.agents.auditor import auditor_agent
from app.agents.chat import chat_agent


@pytest.mark.asyncio
async def test_chat_agent():
    """测试闲聊 Agent"""
    res = await chat_agent.ainvoke({"messages": [HumanMessage(content="你好，你是谁？")]})

    assert "messages" in res
    final_content = res["messages"][-1].content
    assert len(final_content) > 0
    assert "信贷" in final_content or "助手" in final_content


@pytest.mark.asyncio
async def test_auditor_logic():
    """测试审计 Agent 的判断逻辑"""
    user_input = """
    当前信息摘要：
    - 借款企业: 某某光伏科技有限公司
    - 贷款用途: 采购光伏组件
    - 行业分类: 制造业
    - 已传文档数量: 1

    请开始审计决策。
    """
    res = await auditor_agent.ainvoke({"messages": [HumanMessage(content=user_input)]})
    content = res["messages"][-1].content

    # 验证是否输出了合规的 JSON
    import json
    import re

    match = re.search(r"(\{.*\})", content, re.DOTALL)
    assert match is not None
    data = json.loads(match.group(1))

    assert "status" in data
    assert data["status"] in ["PASS", "MISSING"]
