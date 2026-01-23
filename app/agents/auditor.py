from langgraph.prebuilt import create_react_agent

from app.core.prompts import Prompts
from app.services.llm_factory import llm_factory
from app.tools.decision_tool import submit_audit_result
from app.tools.dynamic_tool import create_dynamic_tool
from app.tools.tyc_tool import search_enterprise_info

# 基础工具集
BASE_TOOLS = [search_enterprise_info, submit_audit_result]


def get_auditor_agent(custom_tools_def: list = None):
    """
    动态创建带有自定义工具的 Auditor Agent
    """
    tools = BASE_TOOLS.copy()

    if custom_tools_def:
        for tool_def in custom_tools_def:
            if tool_def.enabled:
                try:
                    dt = create_dynamic_tool(tool_def)
                    tools.append(dt)
                except Exception as e:
                    print(f"Error creating dynamic tool {tool_def.name}: {e}")

    # 使用 langgraph 的 create_react_agent (v1.0.6+ 使用 prompt 参数)
    return create_react_agent(
        model=llm_factory.get_expert_model(),
        tools=tools,
        prompt=Prompts.AUDITOR_SYSTEM,
    )


# 默认实例
auditor_agent = get_auditor_agent()
