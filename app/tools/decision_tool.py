from typing import Literal

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.core.logging import logger


class AuditResult(BaseModel):
    status: Literal["PASS", "MISSING"] = Field(..., description="审计结果：PASS(通过) 或 MISSING(材料缺失)")
    missing_items: list[str] = Field(default_factory=list, description="缺失的材料清单，如果通过则为空")
    guide_message: str = Field(..., description="给用户的自然语言回复，解释结果并引导下一步")
    reason: str = Field(..., description="做出此判定的内部理由")

@tool(args_schema=AuditResult)
def submit_audit_result(status: str, missing_items: list, guide_message: str, reason: str):
    """
    提交审计决策结果。当收集完信息并做出判断后，必须调用此工具来结束审计阶段。
    """
    logger.info(f"[Tool:AuditSubmit] Status: {status} | Reason: {reason}")
    if status == "MISSING":
        logger.warning(f"[Tool:AuditSubmit] Audit Missing: {missing_items}")

    # 这部分内容会被 agent 的 output parser 捕获，但 log 一下更安心
    return "Audit result submitted successfully."
