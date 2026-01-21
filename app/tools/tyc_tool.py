import asyncio

import aiohttp
from langchain_core.tools import tool

from app.core.config import settings
from app.core.logging import logger

BASE_URL = "http://open.api.tianyancha.com"


async def fetch_tyc(session: aiohttp.ClientSession, endpoint: str, params: dict):
    """天眼查 API 调用通用函数 (Session 复用版)"""
    if not settings.TIANYANCHA_TOKEN:
        return {"error": "TIANYANCHA_TOKEN not set"}

    headers = {"Authorization": settings.TIANYANCHA_TOKEN}
    url = f"{BASE_URL}{endpoint}"

    try:
        async with session.get(url, params=params, headers=headers) as resp:
            if resp.status != 200:
                logger.error(f"TYC API Error {endpoint}: HTTP {resp.status}")
                return {"error": f"HTTP {resp.status}"}

            data = await resp.json(content_type=None)

            # error_code=0 表示成功
            if data.get("error_code") != 0:
                logger.warning(f"TYC API Warning {endpoint}: {data.get('reason')}")
                return {"error": data.get("reason", "Unknown error")}

            return data.get("result", {})
    except Exception as e:
        logger.error(f"TYC Connection Error {endpoint}: {e}")
        return {"error": str(e)}


@tool
async def search_enterprise_info(company_name: str) -> str:
    """
    通过天眼查 API 全方位查询企业的工商信息、经营风险和股东背景。
    输入：企业全称（如 '北京百度网讯科技有限公司'）。
    返回：包含基本面、经营异常记录、主要股东结构的综合尽调报告。
    """
    logger.info(f"[TYC] Starting full background check for: {company_name}")

    async with aiohttp.ClientSession() as session:
        # 定义三个任务
        task_base = fetch_tyc(session, "/services/open/ic/baseinfo/normal", {"keyword": company_name})
        task_abnormal = fetch_tyc(
            session, "/services/open/mr/abnormal/2.0", {"keyword": company_name, "pageNum": 1, "pageSize": 20}
        )
        task_holder = fetch_tyc(
            session, "/services/open/ic/holder/2.0", {"keyword": company_name, "pageNum": 1, "pageSize": 20}
        )

        # 并发执行
        res_base, res_abnormal, res_holder = await asyncio.gather(task_base, task_abnormal, task_holder)

        # --- 1. 处理基本信息 ---
        report = f"【天眼查权威尽调报告：{company_name}】\n\n"

        if "error" not in res_base and res_base:
            report += "1. [工商概况]\n"
            report += f"- 法人代表: {res_base.get('legalPersonName')}\n"
            report += f"- 注册资本: {res_base.get('regCapital')}\n"
            report += f"- 成立日期: {res_base.get('estiblishTime')}\n"
            report += f"- 经营状态: {res_base.get('regStatus')}\n"
            report += f"- 统一社会信用代码: {res_base.get('creditCode')}\n"
            report += f"- 行业分类: {res_base.get('industry')}\n"
            report += f"- 注册地址: {res_base.get('regLocation')}\n\n"
        else:
            report += "1. [工商概况] 查询失败或未找到信息。\n\n"

        # --- 2. 处理经营异常 ---
        if "error" not in res_abnormal and res_abnormal:
            items = res_abnormal.get("items", [])
            total = res_abnormal.get("total", 0)
            report += f"2. [经营风险] (共发现 {total} 条异常记录)\n"
            if items:
                for idx, item in enumerate(items[:5], 1):  # 最多显示5条
                    report += f"  {idx}. 列入日期: {item.get('putDate')}\n"
                    report += f"     原因: {item.get('putReason')}\n"
                    report += f"     决定机关: {item.get('putDepartment')}\n"
                    if item.get("removeDate"):
                        report += f"     [已移出] 移出日期: {item.get('removeDate')}\n"
            else:
                report += "- 当前无经营异常记录。\n"
        else:
            report += "2. [经营风险] 查询失败或无数据。\n"
        report += "\n"

        # --- 3. 处理股东信息 ---
        if "error" not in res_holder and res_holder:
            items = res_holder.get("items", [])
            report += "3. [股东结构]\n"
            if items:
                for item in items[:5]:  # 最多显示5个主要股东
                    # 处理 capital 字段兼容性
                    capital_info = item.get("capital", [])
                    percent = "未知"

                    if isinstance(capital_info, list) and capital_info:
                        # 如果是列表，取第一条出资记录的百分比
                        percent = capital_info[0].get("percent", "未知")
                    elif isinstance(capital_info, dict):
                        percent = capital_info.get("percent", "未知")

                    report += f"- {item.get('name')}: 持股/出资 {percent}\n"
            else:
                report += "- 未公开股东信息。\n"
        else:
            report += "3. [股东结构] 查询失败或无数据。\n"

        return report
