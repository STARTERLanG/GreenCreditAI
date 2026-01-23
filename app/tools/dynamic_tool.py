import json
from typing import Any

import httpx
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, create_model

from app.core.logging import logger


class DynamicApiTool(BaseTool):
    name: str
    description: str
    url: str
    method: str
    headers: dict = {}
    args_schema: type[BaseModel]

    def _run(
        self,
        *args: Any,
        run_manager: CallbackManagerForToolRun | None = None,
        **kwargs: Any,
    ) -> str:
        """Execute the API tool."""
        try:
            logger.info(f"[Tool:{self.name}] Calling {self.method} {self.url} with args: {kwargs}")

            # Prepare params/data
            params = {}
            json_data = {}

            if self.method.upper() == "GET":
                params = kwargs
            else:
                json_data = kwargs

            with httpx.Client(timeout=30.0) as client:
                response = client.request(
                    method=self.method,
                    url=self.url,
                    headers=self.headers,
                    params=params,
                    json=json_data,
                )
                response.raise_for_status()

                # Try to parse JSON, fallback to text
                try:
                    return json.dumps(response.json(), ensure_ascii=False)
                except Exception:
                    return response.text

        except httpx.HTTPStatusError as e:
            return f"API Error: {e.response.status_code} - {e.response.text}"
        except Exception as e:
            logger.exception(f"[Tool:{self.name}] Execution failed")
            return f"Execution Error: {str(e)}"


def create_dynamic_tool(tool_def) -> BaseTool:
    """
    根据 CustomToolDefinition 创建 LangChain Tool
    """
    # 1. 解析 Args Schema
    fields = {}
    if tool_def.params:
        try:
            schema = json.loads(tool_def.params)
            props = schema.get("properties", {})
            required = schema.get("required", [])

            for name, prop in props.items():
                is_required = name in required
                default = ... if is_required else None
                desc = prop.get("description", "")

                # Map types (simplified)
                py_type = str
                if prop.get("type") == "number":
                    py_type = float
                elif prop.get("type") == "boolean":
                    py_type = bool
                elif prop.get("type") == "integer":
                    py_type = int

                fields[name] = (py_type, Field(default=default, description=desc))
        except Exception as e:
            logger.error(f"Failed to parse params schema for {tool_def.name}: {e}")

    # 动态创建 Pydantic 模型
    dynamic_args = create_model(f"{tool_def.name}Args", **fields)

    # 2. 解析 Headers
    headers = {}
    if tool_def.headers:
        import contextlib

        with contextlib.suppress(Exception):
            headers = json.loads(tool_def.headers)

    return DynamicApiTool(
        name=tool_def.name,
        description=tool_def.desc,
        url=tool_def.url,
        method=tool_def.method,
        headers=headers,
        args_schema=dynamic_args,
    )
