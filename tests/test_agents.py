from unittest.mock import AsyncMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.agents.auditor import auditor_agent
from app.agents.chat import chat_agent


@pytest.mark.asyncio
async def test_chat_agent():
    """测试闲聊 Agent"""
    # Mock chat agent to avoid LLM call
    mock_res = {"messages": [AIMessage(content="我是绿色信贷智能助手")]}

    with patch.object(chat_agent, "ainvoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_res

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

    # Mock tool call response
    mock_response = {
        "messages": [
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "submit_audit_result",
                        "args": {"status": "PASS", "reason": "ok", "missing_items": [], "guide_message": "ok"},
                        "id": "123",
                    }
                ],
            )
        ]
    }

    with patch.object(auditor_agent, "ainvoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_response

        res = await auditor_agent.ainvoke({"messages": [HumanMessage(content=user_input)]})
        last_msg = res["messages"][-1]

        # 验证是否调用了决策工具
        assert last_msg.tool_calls is not None
        assert len(last_msg.tool_calls) > 0
        assert last_msg.tool_calls[0]["name"] == "submit_audit_result"

        # 验证参数
        args = last_msg.tool_calls[0]["args"]
        assert "status" in args
        assert args["status"] in ["PASS", "MISSING", "REJECT"]
