from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage

from app.agents.auditor import get_auditor_agent
from app.graph.nodes import auditor_node
from app.graph.state import GreenCreditState
from app.schemas.chat import ChatRequest, CustomToolDefinition
from app.services.workflow_service import WorkflowService

# --- 测试数据 ---
SAMPLE_TOOL_DEF = CustomToolDefinition(
    name="stock_search",
    desc="查询股票价格",
    method="GET",
    url="https://api.example.com/stock",
    headers='{"Authorization": "Bearer 123"}',
    params='{"properties": {"symbol": {"type": "string"}}, "required": ["symbol"]}',
    enabled=True,
)


@pytest.mark.asyncio
async def test_request_to_workflow_input():
    """
    验证 ChatRequest 中的 custom_tools 能正确传递给 WorkflowService 的 inputs。
    """
    service = WorkflowService()

    request = ChatRequest(message="test", session_id="123", custom_tools=[SAMPLE_TOOL_DEF])

    with patch.object(service, "_graph") as mock_graph:
        # 模拟 astream_events 返回一个空的异步生成器
        async def mock_stream(*args, **kwargs):
            yield {"event": "on_chain_start", "data": {}, "name": "test"}

        mock_graph.astream_events.side_effect = mock_stream

        # 运行 process_stream (消耗生成器)
        async for _ in service.process_stream(request):
            pass

        # 验证调用参数
        call_args = mock_graph.astream_events.call_args
        assert call_args is not None
        inputs = call_args[0][0]  # 第一个参数是 inputs 字典

        assert "custom_tools" in inputs
        assert len(inputs["custom_tools"]) == 1
        assert inputs["custom_tools"][0].name == "stock_search"


@pytest.mark.asyncio
async def test_auditor_node_uses_dynamic_agent():
    """
    验证 Auditor 节点在接收到 custom_tools 时会调用工厂函数重新构建 Agent。
    """

    state = GreenCreditState(
        session_id="123",
        user_query="查询股价",
        custom_tools=[SAMPLE_TOOL_DEF],
        uploaded_documents=[],
        company_name="测试公司",
        loan_purpose="测试",
        industry_category="科技",
    )

    config = {"configurable": {"thread_id": "123"}}

    # 模拟 get_auditor_agent 以验证它是否被调用
    # 重要：必须在定义它的地方进行 patch，而不是在函数内部导入它的地方
    with patch("app.agents.auditor.get_auditor_agent") as mock_get_agent:
        # 模拟具有异步 ainvoke 行为的智能体实例
        mock_agent_instance = MagicMock()

        async def mock_ainvoke(*args, **kwargs):
            return {"messages": [AIMessage(content="模拟响应")]}

        mock_agent_instance.ainvoke.side_effect = mock_ainvoke
        mock_get_agent.return_value = mock_agent_instance

        # 运行节点
        await auditor_node(state, config)

        # 验证 get_auditor_agent 是否被传入了我们的工具
        mock_get_agent.assert_called_once()
        args = mock_get_agent.call_args[0]
        passed_tools = args[0]

        assert len(passed_tools) == 1
        assert passed_tools[0].name == "stock_search"


def test_agent_factory_binds_tools():
    """
    验证 get_auditor_agent 工厂函数确实将动态工具传递给了 create_react_agent。
    """

    # 模拟 create_react_agent 以检查传入的参数
    with (
        patch("app.agents.auditor.create_react_agent") as mock_create_agent,
        patch("app.services.llm_factory.llm_factory.get_expert_model"),
    ):
        get_auditor_agent([SAMPLE_TOOL_DEF])

        # 获取传递给 create_react_agent 的 'tools' 参数
        call_args = mock_create_agent.call_args
        kwargs = call_args.kwargs
        tools_passed = kwargs.get("tools")

        # 如果不在关键字参数中，检查位置参数（通常是第二个）
        if not tools_passed and len(call_args.args) > 1:
            tools_passed = call_args.args[1]

        tool_names = [t.name for t in tools_passed]

        assert "stock_search" in tool_names
        assert "search_enterprise_info" in tool_names  # 基础工具

        # 验证动态工具的属性
        dynamic_tool = next(t for t in tools_passed if t.name == "stock_search")
        assert dynamic_tool.description == "查询股票价格"
        assert dynamic_tool.method == "GET"
        assert "Authorization" in dynamic_tool.headers
