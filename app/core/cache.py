import functools
from collections.abc import Callable
from typing import Any

from app.core.logging import logger

# 全局工具缓存：{tool_name: {query_hash: result}}
# 这种结构允许不同工具对同一 query 有不同的缓存
GLOBAL_TOOL_CACHE: dict[str, dict[str, Any]] = {}


def tool_cache(func: Callable) -> Callable:
    """
    通用工具缓存装饰器。
    基于工具函数名 + 第一个参数(query) 进行缓存。
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # 获取工具名
        tool_name = func.__name__

        # 尝试获取 query (通常是第一个参数)
        # LangChain Tool 的参数可能是位置参数或关键字参数
        query = None
        if args:
            query = str(args[0])
        elif kwargs:
            # 取第一个 value 作为 query key
            query = str(next(iter(kwargs.values())))

        if not query:
            # 如果没参数，不缓存，直接运行
            return await func(*args, **kwargs)

        # 初始化该工具的缓存桶
        if tool_name not in GLOBAL_TOOL_CACHE:
            GLOBAL_TOOL_CACHE[tool_name] = {}

        # 检查命中
        if query in GLOBAL_TOOL_CACHE[tool_name]:
            logger.info(f"[Cache HIT] Tool: {tool_name} | Query: {query[:20]}...")
            return GLOBAL_TOOL_CACHE[tool_name][query]

        # 未命中，执行并写入
        logger.info(f"[Cache MISS] Tool: {tool_name} | Query: {query[:20]}...")
        result = await func(*args, **kwargs)

        # 只有成功的结果才缓存 (防止报错也被缓存)
        if result and "error" not in str(result).lower():
            GLOBAL_TOOL_CACHE[tool_name][query] = result

        return result

    return wrapper
