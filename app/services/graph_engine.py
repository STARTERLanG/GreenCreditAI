from langgraph.graph import StateGraph, START, END
from app.schemas.state import GreenCreditState
from app.agents.nodes import (
    router_node, chat_node, extractor_node, 
    policy_enrichment_node, auditor_node
)

def create_base_graph():
    """定义基础拓扑结构，不绑定持久化器"""
    workflow = StateGraph(GreenCreditState)

    workflow.add_node("router", router_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("enrichment", policy_enrichment_node)
    workflow.add_node("auditor", auditor_node)

    workflow.add_edge(START, "router")

    def router_condition(state: GreenCreditState):
        intent = state["current_intent"]
        if intent == "GENERAL_CHAT":
            return "chat"
        return "extractor"

    workflow.add_conditional_edges("router", router_condition, {"chat": "chat", "extractor": "extractor"})
    workflow.add_edge("extractor", "auditor")

    def audit_decision(state: GreenCreditState):
        if state.get("is_completed"): return END
        return "enrichment"

    workflow.add_conditional_edges("auditor", audit_decision, {"enrichment": "enrichment", END: END})
    workflow.add_edge("chat", END)
    workflow.add_edge("enrichment", END)

    return workflow