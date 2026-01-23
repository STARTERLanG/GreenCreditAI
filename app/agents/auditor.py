from langchain.agents import create_agent

from app.core.prompts import Prompts
from app.services.llm_factory import llm_factory
from app.tools.decision_tool import submit_audit_result
from app.tools.tyc_tool import search_enterprise_info

# 给 Auditor 加上决策提交工具，实现结构化输出
auditor_agent = create_agent(
    model=llm_factory.get_expert_model(),
    tools=[search_enterprise_info, submit_audit_result],
    system_prompt=Prompts.AUDITOR_SYSTEM,
)
