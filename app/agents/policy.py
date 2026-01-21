from langchain.agents import create_agent

from app.core.prompts import Prompts
from app.services.llm_factory import llm_factory
from app.tools.rag_tool import search_green_policy

policy_agent = create_agent(
    model=llm_factory.get_expert_model(), tools=[search_green_policy], system_prompt=Prompts.POLICY_AGENT_SYSTEM
)
