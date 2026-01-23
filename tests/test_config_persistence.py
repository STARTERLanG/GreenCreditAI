import pytest
from app.models.config import AgentTool, McpServer, SystemSetting
from app.services.config_service import config_service
from sqlmodel import Session, select
from app.core.db import engine

@pytest.mark.asyncio
async def test_system_settings_persistence():
    """测试系统设置(Key-Value)的持久化逻辑"""
    test_key = "test_theme"
    test_value = "dark_mode"
    
    # 1. 保存设置
    config_service.update_setting(test_key, test_value)
    
    # 2. 读取验证
    settings = config_service.get_all_settings()
    assert test_key in settings
    assert settings[test_key] == test_value
    
    # 3. 更新验证
    new_value = "light_mode"
    config_service.update_setting(test_key, new_value)
    settings = config_service.get_all_settings()
    assert settings[test_key] == new_value

@pytest.mark.asyncio
async def test_agent_tool_persistence():
    """测试自定义 API 工具的持久化逻辑 (包含 JSON 字符串字段)"""
    tool_id = "test-tool-123"
    tool_name = "weather_api"
    
    # 创建模型对象
    new_tool = AgentTool(
        id=tool_id,
        name=tool_name,
        desc="查询天气",
        method="GET",
        url="api.weather.com",
        headers='{"Auth": "Key"}',
        params='{"city": "string"}',
        enabled=True
    )
    
    # 1. 保存
    saved = config_service.save_tool(new_tool)
    assert saved.id == tool_id
    
    # 2. 列表查询验证
    tools = config_service.list_tools()
    assert any(t.id == tool_id for t in tools)
    
    # 3. 修改验证
    new_tool.desc = "更新后的描述"
    config_service.save_tool(new_tool)
    tools = config_service.list_tools()
    updated_tool = next(t for t in tools if t.id == tool_id)
    assert updated_tool.desc == "更新后的描述"
    
    # 4. 删除验证
    config_service.delete_tool(tool_id)
    tools = config_service.list_tools()
    assert not any(t.id == tool_id for t in tools)

@pytest.mark.asyncio
async def test_mcp_server_persistence():
    """测试 MCP 服务配置的持久化逻辑"""
    mcp_id = "test-mcp-456"
    
    new_mcp = McpServer(
        id=mcp_id,
        name="test-server",
        type="stdio",
        command="npx",
        args='["run", "server"]',
        enabled=True
    )
    
    # 1. 保存
    config_service.save_mcp_server(new_mcp)
    
    # 2. 查询
    servers = config_service.list_mcp_servers()
    assert any(s.id == mcp_id for s in servers)
    
    # 3. 删除
    config_service.delete_mcp_server(mcp_id)
    servers = config_service.list_mcp_servers()
    assert not any(s.id == mcp_id for s in servers)
