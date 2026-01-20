from typing import TypedDict, List, Annotated, Optional
import operator

class GreenCreditState(TypedDict):
    # --- 基础输入 ---
    session_id: str                 # 唯一会话ID
    user_query: str                 # 用户当前输入
    uploaded_documents: Annotated[List[str], operator.add]   # 累计提取后的文档内容
    
    # --- 核心实体 ---
    company_name: Optional[str]     # 借款主体
    loan_purpose: Optional[str]     # 贷款用途
    industry_category: Optional[str] # 归属行业
    
    # --- 证据层 ---
    # 使用 Annotated[..., operator.add] 允许列表内容不断追加而非覆盖
    web_evidence: Annotated[List[str], operator.add]   # 联网搜索信息 (Placeholder)
    rag_standards: Annotated[List[str], operator.add]  # 匹配到的政策标准
    
    # --- 决策层 ---
    analysis_history: List[str]     # 历次思考记录
    missing_materials: List[str]    # 缺失材料清单
    final_report: Optional[str]     # 最终 Markdown 报告
    
    # --- 控制流 ---
    next_node: str                  # 手动控制流向 (可选)
    current_intent: str             # router 判定出的意图
    is_completed: bool              # 任务是否结束
