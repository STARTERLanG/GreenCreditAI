from langchain.agents import create_agent

from app.core.prompts import Prompts
from app.services.llm_factory import llm_factory

# Auditor 不需要工具，但使用 Agent 架构方便未来扩展
# 注意：如果 langchain 版本较旧，create_agent 可能不存在，需确认环境
auditor_agent = create_agent(model=llm_factory.get_expert_model(), tools=[], system_prompt=Prompts.AUDITOR_SYSTEM)
