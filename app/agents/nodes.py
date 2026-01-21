import json
import re
from typing import Any

from langgraph.prebuilt import create_react_agent

from app.agents.router import router_agent
from app.core.logging import logger
from app.core.prompts import Prompts
from app.schemas.state import GreenCreditState
from app.services.llm_factory import llm_factory
from app.tools.rag_tool import search_green_policy


async def router_node(state: GreenCreditState) -> dict[str, Any]:
    """判定意图：是闲聊还是在办业务（查政策/投项目）"""
    from app.services.session_service import session_service

    history = session_service.get_chat_history(state["session_id"], limit=3)
    intent = await router_agent.route(state["user_query"], chat_history=history)
    return {"current_intent": intent.value}


def extract_json(text: str) -> dict:
    """从文本中提取并解析 JSON 块"""
    if not text or not text.strip():
        logger.error("LLM returned an empty string.")
        return {}

    try:
        # 尝试匹配 ```json { ... } ``` 块
        match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # 尝试直接匹配第一个 { 到最后一个 }
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
        return json.loads(text.strip())
    except Exception as e:
        logger.error(f"JSON parsing failed: {e} | Raw content: {text}")
        return {}


async def extractor_node(state: GreenCreditState) -> dict[str, Any]:
    """
    核心提取节点：
    如果用户上传了文件，全力解析文件。
    """
    if not state.get("uploaded_documents"):
        logger.info("[Extractor] No documents to extract.")
        return {"analysis_history": ["当前无上传文件"]}

    llm = llm_factory.get_expert_model()
    all_docs_content = "\n\n".join(state["uploaded_documents"])

    logger.info(f"[Extractor] Processing documents. Total length: {len(all_docs_content)}")

    prompt = Prompts.EXTRACTOR_SYSTEM.format(content=all_docs_content[:30000])

    try:
        res = await llm.ainvoke(prompt)
        data = extract_json(res.content)

        return {
            "company_name": data.get("company_name"),
            "loan_purpose": data.get("loan_purpose"),
            "industry_category": data.get("industry"),
            "analysis_history": [f"已从文件中提取实体: {data.get('company_name')}"],
        }
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return {"analysis_history": [f"文件解析提取失败: {str(e)}"]}


async def auditor_node(state: GreenCreditState) -> dict[str, Any]:
    """
    审计决策节点：
    利用大模型评估当前材料的完整性。
    """
    llm = llm_factory.get_expert_model()

    # 构建当前信息的摘要
    info_summary = f"""
    - 借款企业: {state.get("company_name") or "未知"}
    - 贷款用途: {state.get("loan_purpose") or "未知"}
    - 行业分类: {state.get("industry_category") or "未知"}
    - 已传文档数量: {len(state.get("uploaded_documents", []))}
    """

    prompt = Prompts.AUDITOR_SYSTEM.format(info_summary=info_summary, user_query=state.get("user_query"))

    try:
        res = await llm.ainvoke(prompt)
        content = res.content if hasattr(res, "content") else str(res)
        logger.info(f"[Auditor Raw Output]: {content}")

        data = extract_json(content)
        if not data:
            raise ValueError("Failed to extract valid JSON from LLM response")

        status = data.get("status", "MISSING")

        if status == "PASS":
            return {"is_completed": False, "analysis_history": ["审计通过。"]}
        else:
            return {
                "final_report": data.get("guide_message", "请补充材料。"),
                "missing_materials": data.get("missing_items", []),
                "is_completed": True,
                "analysis_history": [f"审计未通过：{data.get('reason')}"],
            }

    except Exception as e:
        logger.error(f"Auditor node error: {e}")
        # 降级处理
        return {
            "final_report": "审核中遇到一点小问题，请确保您已上传企业名称和用途相关的文档。",
            "is_completed": True,
        }


async def chat_node(state: GreenCreditState) -> dict[str, Any]:
    """闲聊节点 (支持历史上下文回溯)"""
    from app.services.session_service import session_service

    # 获取最近 10 条历史
    history = session_service.get_chat_history(state["session_id"], limit=10)

    llm = llm_factory.get_router_model()

    # 将 LangChain 消息对象转换为文本上下文
    history_text = "\n".join([f"{msg.type}: {msg.content}" for msg in history])

    prompt = Prompts.CHAT_SYSTEM.format(history=history_text, user_query=state["user_query"])

    res = await llm.ainvoke(prompt)
    return {"final_report": res.content, "is_completed": True}


async def policy_enrichment_node(state: GreenCreditState) -> dict[str, Any]:
    """
    政策分析节点 (ReAct Agent)
    具备自主调用 search_green_policy 工具的能力。
    """
    llm = llm_factory.get_expert_model()

    # 定义工具列表
    tools = [search_green_policy]

    # 创建 ReAct Agent
    agent_executor = create_react_agent(llm, tools)

    # 构造 Prompt (这里我们作为 user message 传入，或者修改 create_react_agent 的 system_message 参数)
    # create_react_agent 支持 `state_modifier` 参数来设置 System Prompt

    company = state.get("company_name", "未知企业")
    purpose = state.get("loan_purpose", "未知用途")
    industry = state.get("industry_category", "未知行业")

    user_msg = Prompts.POLICY_AGENT_SYSTEM.format(company=company, industry=industry, purpose=purpose)

    # 调用 Agent
    response = await agent_executor.ainvoke({"messages": [("user", user_msg)]})

    # 提取最后一条 AI 消息的内容
    final_message = response["messages"][-1]

    return {
        "final_report": final_message.content,
        "is_completed": True,
        "analysis_history": ["Policy Agent 完成了分析。"],
    }
