import json
import re
from typing import Any

from langchain_core.messages import HumanMessage

from app.agents.auditor import auditor_agent
from app.agents.chat import chat_agent
from app.agents.policy import policy_agent
from app.agents.router import router_agent
from app.core.logging import logger
from app.core.prompts import Prompts
from app.graph.state import GreenCreditState
from app.services.llm_factory import llm_factory


# --- 1. Router Node ---
async def router_node(state: GreenCreditState) -> dict[str, Any]:
    """判定意图"""
    from app.services.session_service import session_service

    history = session_service.get_chat_history(state["session_id"], limit=3)
    intent = await router_agent.route(state["user_query"], chat_history=history)
    return {"current_intent": intent.value}


# --- 2. Extractor Node (Chain) ---
async def extractor_node(state: GreenCreditState) -> dict[str, Any]:
    """信息提取"""
    if not state.get("uploaded_documents"):
        return {"analysis_history": ["当前无上传文件"]}

    llm = llm_factory.get_expert_model()
    all_docs_content = "\n\n".join(state["uploaded_documents"])
    prompt = Prompts.EXTRACTOR_SYSTEM.format(content=all_docs_content[:30000])

    try:
        res = await llm.ainvoke(prompt)
        data = extract_json(res.content)
        return {
            "company_name": data.get("company_name"),
            "loan_purpose": data.get("loan_purpose"),
            "industry_category": data.get("industry"),
            "analysis_history": [f"已提取实体: {data.get('company_name')}"],
        }
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return {"analysis_history": [f"提取失败: {str(e)}"]}


# --- 3. Auditor Node ---
async def auditor_node(state: GreenCreditState) -> dict[str, Any]:
    """审计决策智能体节点"""
    info_summary = f"""
    - 借款企业: {state.get("company_name") or "未知"}
    - 贷款用途: {state.get("loan_purpose") or "未知"}
    - 行业分类: {state.get("industry_category") or "未知"}
    - 已传文档数量: {len(state.get("uploaded_documents", []))}
    """

    user_input = f"""
    当前信息摘要：
    {info_summary}
    用户最新指令：{state.get("user_query")}

    请开始审计决策。
    """

    # create_agent 返回的是 Graph，输入是 messages 列表
    res = await auditor_agent.ainvoke({"messages": [HumanMessage(content=user_input)]})
    # 提取最后一条消息
    content = res["messages"][-1].content

    data = extract_json(content)
    if not data:
        return {"final_report": "审核遇到异常，请重试。", "is_completed": True}

    if data.get("status") == "PASS":
        return {"is_completed": False, "analysis_history": ["审计通过。"]}
    else:
        return {
            "final_report": data.get("guide_message", "请补充材料。"),
            "missing_materials": data.get("missing_items", []),
            "is_completed": True,
            "analysis_history": [f"审计拦截: {data.get('reason')}"],
        }


# --- 4. Policy Enrichment Node ---
async def policy_enrichment_node(state: GreenCreditState) -> dict[str, Any]:
    """政策专家智能体节点"""
    company = state.get("company_name", "未知企业")
    purpose = state.get("loan_purpose", "未知用途")
    industry = state.get("industry_category", "未知行业")

    user_input = f"""
    企业: {company}
    行业: {industry}
    用途: {purpose}

    请开始合规性分析。
    """

    res = await policy_agent.ainvoke({"messages": [HumanMessage(content=user_input)]})
    final_report = res["messages"][-1].content

    return {
        "final_report": final_report,
        "is_completed": True,
        "analysis_history": ["Policy Expert 完成了深度分析。"],
    }


# --- 5. Chat Node ---
async def chat_node(state: GreenCreditState) -> dict[str, Any]:
    """闲聊智能体节点"""
    from app.services.session_service import session_service

    history = session_service.get_chat_history(state["session_id"], limit=10)
    history_text = "\n".join([f"{msg.type}: {msg.content}" for msg in history])

    user_input = f"""
    [对话历史]
    {history_text}

    用户输入：{state["user_query"]}
    """

    res = await chat_agent.ainvoke({"messages": [HumanMessage(content=user_input)]})
    return {"final_report": res["messages"][-1].content, "is_completed": True}


# --- Helpers ---
def extract_json(text: str) -> dict:
    if not text or not text.strip():
        return {}
    try:
        match = re.search(r"```json\s*(\{.*\})\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
        return json.loads(text.strip())
    except Exception:
        return {}
