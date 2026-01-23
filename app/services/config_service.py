from sqlmodel import Session, select

from app.core.db import engine
from app.models.config import AgentTool, McpServer, SystemSetting


class ConfigService:
    # --- System Settings ---
    def get_all_settings(self) -> dict:
        """获取所有设置项并组装成字典"""
        with Session(engine) as session:
            results = session.exec(select(SystemSetting)).all()
            return {item.key: item.value for item in results}

    def update_setting(self, key: str, value: str):
        """更新或创建设置项"""
        with Session(engine) as session:
            existing = session.get(SystemSetting, key)
            if existing:
                existing.value = value
                session.add(existing)
            else:
                new_item = SystemSetting(key=key, value=value)
                session.add(new_item)
            session.commit()

    # --- Agent Tool ---
    def list_tools(self) -> list[AgentTool]:
        with Session(engine) as session:
            return list(session.exec(select(AgentTool)).all())

    def save_tool(self, tool: AgentTool) -> AgentTool:
        with Session(engine) as session:
            existing = session.get(AgentTool, tool.id)
            if existing:
                # Update fields
                existing.name = tool.name
                existing.desc = tool.desc
                existing.method = tool.method
                existing.url = tool.url
                existing.headers = tool.headers
                existing.params = tool.params
                existing.examples = tool.examples
                existing.enabled = tool.enabled
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                session.add(tool)
                session.commit()
                session.refresh(tool)
                return tool

    def delete_tool(self, tool_id: str) -> bool:
        with Session(engine) as session:
            tool = session.get(AgentTool, tool_id)
            if tool:
                session.delete(tool)
                session.commit()
                return True
            return False

    # --- MCP Server ---
    def list_mcp_servers(self) -> list[McpServer]:
        with Session(engine) as session:
            return list(session.exec(select(McpServer)).all())

    def save_mcp_server(self, server: McpServer) -> McpServer:
        with Session(engine) as session:
            existing = session.get(McpServer, server.id)
            if existing:
                existing.name = server.name
                existing.type = server.type
                existing.command = server.command
                existing.args = server.args
                existing.env = server.env
                existing.enabled = server.enabled
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                session.add(server)
                session.commit()
                session.refresh(server)
                return server

    def delete_mcp_server(self, server_id: str) -> bool:
        with Session(engine) as session:
            server = session.get(McpServer, server_id)
            if server:
                session.delete(server)
                session.commit()
                return True
            return False


config_service = ConfigService()
