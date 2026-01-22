import asyncio
from typing import Any

from langchain_core.callbacks import AsyncCallbackHandler

from app.core.logging import logger


class WorkflowAsyncCallbackHandler(AsyncCallbackHandler):
    """
    流式回调处理器（Debug 增强版）：
    1. 屏蔽 Router/Auditor/Extractor 的 Token。
    2. 透传 Policy/Chat 的 Token。
    3. 详细记录所有动作日志用于排查。
    """
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        # 黑名单：这些节点的输出绝对不能作为 Token 发送给用户
        self.blacklist_runs = ["auditor", "router", "extractor"]

    async def on_llm_start(self, serialized: dict[str, Any], prompts: list[str], **kwargs: Any) -> Any:
        run_name = kwargs.get("name", "Unknown").lower()
        logger.info(f"[Callback] LLM Start | Name: {run_name}")

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> Any:
        """捕获 LLM 实时生成的 Token"""
        run_name = kwargs.get("name", "").lower()

        # 检查是否在黑名单
        is_blocked = any(name in run_name for name in self.blacklist_runs)

        if is_blocked:
            # 调试日志：采样打印被屏蔽的 Token，防止日志爆炸
            # logger.debug(f"[Callback] BLOCKED token from {run_name}: {token}")
            return

        if token:
            # 调试日志：记录放行的 Token (仅在极度调试时开启，平时注释掉以免刷屏)
            # logger.debug(f"[Callback] STREAMING token from {run_name}: {repr(token)}")
            await self.queue.put({"type": "token", "content": token})

    async def on_tool_start(
        self, serialized: dict[str, Any], input_str: str, **kwargs: Any
    ) -> Any:
        tool_name = serialized.get("name", "Unknown Tool")
        logger.info(f"[Callback] Tool Start | Name: {tool_name} | Input: {input_str[:100]}...")

        tool_call_id = kwargs.get("run_id") or str(id(input_str))
        payload = {
            "type": "tool_call",
            "id": str(tool_call_id),
            "name": tool_name,
            "input": input_str,
            "status": "running"
        }
        await self.queue.put({"type": "think", "content": payload})

    async def on_tool_end(self, output: str, **kwargs: Any) -> Any:
        logger.info(f"[Callback] Tool End | Output len: {len(str(output))}")
        tool_call_id = kwargs.get("run_id")
        payload = {
            "type": "tool_call",
            "id": str(tool_call_id),
            "output": output,
            "status": "completed"
        }
        await self.queue.put({"type": "think", "content": payload})

    async def on_tool_error(self, error: Exception, **kwargs: Any) -> Any:
        logger.error(f"[Callback] Tool Error: {error}")
        await self.queue.put({"type": "think", "content": f"工具执行出错: {str(error)}"})
