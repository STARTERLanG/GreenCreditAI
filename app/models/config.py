from uuid import uuid4

from sqlmodel import Field, SQLModel


class AgentTool(SQLModel, table=True):
    """自定义 API 工具配置"""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True)
    desc: str
    method: str
    url: str
    headers: str | None = None  # JSON string
    params: str | None = None  # JSON string
    examples: str | None = None  # JSON string (list)
    enabled: bool = True
    user_id: str | None = Field(default=None, index=True, description="Owner")
    created_at: int = Field(default_factory=lambda: 0)  # Timestamp


class McpServer(SQLModel, table=True):
    """MCP 服务配置"""

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    name: str = Field(index=True)
    type: str  # stdio / sse
    command: str
    args: str | None = None  # JSON string (list)
    env: str | None = None  # JSON string (dict)
    enabled: bool = True
    user_id: str | None = Field(default=None, index=True, description="Owner")
    created_at: int = Field(default_factory=lambda: 0)


class SystemSetting(SQLModel, table=True):
    """全局系统/用户设置 (Key-Value 结构)"""

    key: str = Field(primary_key=True)
    value: str  # JSON 字符串内容
