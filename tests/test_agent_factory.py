from unittest.mock import MagicMock, patch

import pytest

from app.agents.auditor import get_auditor_agent
from app.schemas.chat import CustomToolDefinition


# 模拟 LLM 工厂以避免真实的 API 调用
@pytest.fixture
def mock_llm():
    with patch("app.services.llm_factory.llm_factory.get_expert_model") as mock:
        # 模拟一个简单的可运行对象行为
        mock_model = MagicMock()
        mock.return_value = mock_model
        yield mock_model


@pytest.mark.asyncio
async def test_get_auditor_agent_default(mock_llm):
    """
    测试创建默认的审计智能体（不带自定义工具）。
    应返回一个有效的已编译图对象（可运行）。
    """
    try:
        agent = get_auditor_agent()
        assert agent is not None
        # 验证它是一个已编译的图（具有 ainvoke 方法）
        assert hasattr(agent, "ainvoke")
    except TypeError as e:
        pytest.fail(f"由于类型错误导致创建智能体失败（可能是参数不匹配）：{e}")
    except Exception as e:
        pytest.fail(f"发生了意外错误：{e}")


@pytest.mark.asyncio
async def test_get_auditor_agent_with_custom_tools(mock_llm):
    """
    测试使用动态自定义工具创建审计智能体。
    应成功将新工具绑定到智能体。
    """
    custom_tools = [
        CustomToolDefinition(
            name="test_tool", desc="测试工具", method="GET", url="https://httpbin.org/get", enabled=True
        )
    ]

    try:
        agent = get_auditor_agent(custom_tools)
        assert agent is not None
        assert hasattr(agent, "ainvoke")
        # 虽然不方便直接检查已编译图内部的受保护工具列表，
        # 但成功创建意味着 create_react_agent 接受了合并后的工具列表。
    except Exception as e:
        pytest.fail(f"创建动态智能体失败：{e}")
