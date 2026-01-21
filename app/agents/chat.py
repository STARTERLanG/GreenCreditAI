from langchain.agents import create_agent

from app.core.prompts import Prompts
from app.services.llm_factory import llm_factory

chat_agent = create_agent(model=llm_factory.get_router_model(), tools=[], system_prompt=Prompts.CHAT_SYSTEM)
