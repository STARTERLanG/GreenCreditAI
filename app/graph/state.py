import operator
from typing import Annotated, Any, TypedDict


class GreenCreditState(TypedDict):
    # --- 基础输入 ---
    session_id: str  # 唯一会话ID
    user_query: str  # 用户当前输入
    uploaded_documents: Annotated[list[str], operator.add]  # 累计提取后的文档内容

    # --- 核心实体 ---
    company_name: str | None  # 借款主体
    loan_purpose: str | None  # 贷款用途
    industry_category: str | None  # 归属行业

    # --- 证据层 ---
    # 使用 Annotated[..., operator.add] 允许列表内容不断追加而非覆盖
    web_evidence: Annotated[list[str], operator.add]  # 联网搜索信息 (Placeholder)
    rag_standards: Annotated[list[str], operator.add]  # 匹配到的政策标准

    # --- 决策层 ---
    analysis_history: list[str]  # 历次思考记录
    missing_materials: list[str]  # 缺失材料清单
    final_report: str | None  # 最终 Markdown 报告

    # --- 控制流 ---
    next_node: str  # 手动控制流向 (可选)
    current_intent: str  # router 判定出的意图
    is_completed: bool  # 任务是否结束
    custom_tools: list[Any]  # 动态工具定义
