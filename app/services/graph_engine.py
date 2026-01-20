from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from app.schemas.state import GreenCreditState
from app.agents.nodes import (
    router_node, chat_node, extractor_node, 
    policy_enrichment_node, auditor_node
)

def create_graph():
    workflow = StateGraph(GreenCreditState)

    # 1. 添加节点
    workflow.add_node("router", router_node)
    workflow.add_node("chat", chat_node)
    workflow.add_node("extractor", extractor_node)
    workflow.add_node("enrichment", policy_enrichment_node)
    workflow.add_node("auditor", auditor_node)

    # 2. 定义入口 (新版语法)
    workflow.add_edge(START, "router")

    # 3. 定义条件边缘与普通边缘 (Edges)

    # 路由分流
    def router_condition(state: GreenCreditState):
        intent = state["current_intent"]
        if intent == "GENERAL_CHAT":
            return "chat"
        return "extractor"

    workflow.add_conditional_edges(
        "router", 
        router_condition,
        {
            "chat": "chat",
            "extractor": "extractor"
        }
    )

    # 提取完成后进入审计
    workflow.add_edge("extractor", "auditor")

    # 审计后的决策：继续深度分析还是停下来要材料
    def audit_decision(state: GreenCreditState):
        if state.get("is_completed"):
            return END
        return "enrichment"

    workflow.add_conditional_edges(
        "auditor", 
        audit_decision,
        {
            "enrichment": "enrichment",
            END: END
        }
    )

    # 辅助节点处理
    workflow.add_edge("chat", END)
    workflow.add_edge("enrichment", END)

    # 4. 编译时加入 checkpointer
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)

graph_app = create_graph()
