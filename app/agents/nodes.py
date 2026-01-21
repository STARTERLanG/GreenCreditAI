import json
import re

from typing import Dict, Any
from app.agents.router import router_agent
from app.services.llm_factory import llm_factory
from app.schemas.state import GreenCreditState
from app.core.logging import logger

async def router_node(state: GreenCreditState) -> Dict[str, Any]:
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
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        # 尝试直接匹配第一个 { 到最后一个 }
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return json.loads(match.group(1).strip())
        return json.loads(text.strip())
    except Exception as e:
        logger.error(f"JSON parsing failed: {e} | Raw content: {text}")
        return {}

async def extractor_node(state: GreenCreditState) -> Dict[str, Any]:
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

    prompt = f"""你是一个信贷预审员。请从以下文档内容中提取核心信息。
要求：
1. 必须以 JSON 格式返回。
2. 不要包含任何解释性文字。

需要提取的字段：
- company_name: 企业全称
- loan_purpose: 贷款具体用途
- industry: 所属行业分类

文档内容：
{all_docs_content[:30000]} 
"""
    
    try:
        res = await llm.ainvoke(prompt)
        data = extract_json(res.content)
        
        return {
            "company_name": data.get("company_name"),
            "loan_purpose": data.get("loan_purpose"),
            "industry_category": data.get("industry"),
            "analysis_history": [f"已从文件中提取实体: {data.get('company_name')}"]
        }
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return {"analysis_history": [f"文件解析提取失败: {str(e)}"]}

async def auditor_node(state: GreenCreditState) -> Dict[str, Any]:
    """
    审计决策节点：
    利用大模型评估当前材料的完整性。
    """
    llm = llm_factory.get_expert_model()
    
    # 构建当前信息的摘要
    info_summary = f"""
    - 借款企业: {state.get('company_name') or '未知'}
    - 贷款用途: {state.get('loan_purpose') or '未知'}
    - 行业分类: {state.get('industry_category') or '未知'}
    - 已传文档数量: {len(state.get('uploaded_documents', []))}
    """
    
    prompt = f"""你是一个资深的绿色信贷审查员。你的任务是评估当前收集到的信息是否足以进行深度合规性分析。

当前信息摘要：
{info_summary}
用户最新指令：{state.get('user_query')}

评估准则：
1. 正常情况下：必须有企业全称、具体贷款用途、且至少有一份文档。
2. 例外情况：如果用户明确要求直接分析，则必须 PASS。

请给出你的结论。必须以 JSON 格式输出，不要包含任何多余文字：
{{
  "status": "PASS" 或 "MISSING",
  "missing_items": ["缺失项1", "缺失项2"], 
  "guide_message": "给用户的温馨提示语",
  "reason": "你做出此判断的内部理由"
}}
"""

    try:
        res = await llm.ainvoke(prompt)
        content = res.content if hasattr(res, 'content') else str(res)
        logger.info(f"[Auditor Raw Output]: {content}")
        
        data = extract_json(content)
        if not data:
            raise ValueError("Failed to extract valid JSON from LLM response")
        
        status = data.get("status", "MISSING")
        
        # 逻辑检查：如果用户说“分析一下”，但模型因为没文档判为 MISSING，这里增加一层语义检查（可选，但 Prompt 已经强调了）
        
        if status == "PASS":
            return {
                "is_completed": False,
                "analysis_history": ["审计通过。"]
            }
        else:
            return {
                "final_report": data.get("guide_message", "请补充材料。"),
                "missing_materials": data.get("missing_items", []),
                "is_completed": True,
                "analysis_history": [f"审计未通过：{data.get('reason')}"]
            }
            
    except Exception as e:
        logger.error(f"Auditor node error: {e}")
        # 降级处理
        return {
            "final_report": "审核中遇到一点小问题，请确保您已上传企业名称和用途相关的文档。",
            "is_completed": True
        }

async def chat_node(state: GreenCreditState) -> Dict[str, Any]:
    """闲聊节点 (支持历史上下文回溯)"""
    from app.services.session_service import session_service
    # 获取最近 10 条历史
    history = session_service.get_chat_history(state["session_id"], limit=10)
    
    llm = llm_factory.get_router_model()
    
    # 将 LangChain 消息对象转换为文本上下文
    history_text = "\n".join([f"{msg.type}: {msg.content}" for msg in history])
    
    prompt = f"""你是一个绿色信贷智能助手。请回答用户的输入。
如果用户是在问关于之前的对话内容，请参考以下历史记录。
如果用户只是打招呼，请礼貌回应。

[对话历史]
{history_text}

用户输入：{state['user_query']}"""

    res = await llm.ainvoke(prompt)
    return {"final_report": res.content, "is_completed": True}

async def policy_enrichment_node(state: GreenCreditState) -> Dict[str, Any]:
    """真正的 RAG 分析节点"""
    from app.agents.policy import policy_agent
    # 调用之前的专家逻辑
    query = f"{state['company_name']} {state['loan_purpose']} {state['industry_category']}"
    
    full_text = ""
    async for chunk in policy_agent.run(query):
        full_text += chunk
    
    return {"final_report": full_text, "is_completed": True}