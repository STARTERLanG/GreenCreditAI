import json

from fastapi import APIRouter, HTTPException

from app.models.config import AgentTool, McpServer
from app.schemas.chat import CustomToolDefinition, McpServerDefinition
from app.services.config_service import config_service

router = APIRouter()


# --- System Settings ---
@router.get("/settings")
async def get_settings():
    """获取所有全局设置"""
    return config_service.get_all_settings()


@router.post("/settings")
async def update_settings(payload: dict):
    """批量更新设置"""
    for k, v in payload.items():
        # v 如果是对象，转为字符串存储
        val_str = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
        config_service.update_setting(k, val_str)
    return {"status": "success"}


# --- Tools ---
@router.get("/tools")
async def list_tools():
    return config_service.list_tools()


@router.post("/tools")
async def save_tool(tool_def: CustomToolDefinition):
    # Convert Schema to DB Model
    # headers/params are already strings from frontend
    # examples is list -> string
    tool = AgentTool(
        id=tool_def.id,
        name=tool_def.name,
        desc=tool_def.desc,
        method=tool_def.method,
        url=tool_def.url,
        headers=tool_def.headers,
        params=tool_def.params,
        examples=json.dumps(tool_def.examples, ensure_ascii=False) if tool_def.examples else None,
        enabled=tool_def.enabled,
    )
    return config_service.save_tool(tool)


@router.delete("/tools/{tool_id}")
async def delete_tool(tool_id: str):
    success = config_service.delete_tool(tool_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"status": "success"}


# --- MCP ---
@router.get("/mcp")
async def list_mcp():
    return config_service.list_mcp_servers()


@router.post("/mcp")
async def save_mcp(server_def: McpServerDefinition):
    # Convert Schema to DB Model
    # args is list -> string
    # env is dict -> string
    server = McpServer(
        id=server_def.id,
        name=server_def.name,
        type=server_def.type,
        command=server_def.command,
        args=json.dumps(server_def.args, ensure_ascii=False) if server_def.args else None,
        env=json.dumps(server_def.env, ensure_ascii=False) if server_def.env else None,
        enabled=server_def.enabled,
    )
    return config_service.save_mcp_server(server)


@router.delete("/mcp/{server_id}")
async def delete_mcp(server_id: str):
    success = config_service.delete_mcp_server(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"status": "success"}
