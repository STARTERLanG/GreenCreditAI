---
trigger: always_on
---


# 项目核心原则

## 技术攻坚原则 (Critical)
- **拒绝妥协**: 在遇到技术难题（如 API 变更、版本不兼容、逻辑 Bug）时，必须深入挖掘根源（通过代码自省、文档分析等），寻找正统的解决方案。
- **严禁阉割**: 严禁通过简单移除功能或降低标准来规避技术挑战。必须保证功能的完整性与系统的专业性。

## 语言要求 (Critical)
- **强制中文**: 所有生成内容（包括思考过程、代码注释、文档、回复消息）**必须**使用简体中文。
- **Exception**: 代码中的变量名、函数名、类名等标识符保持英文。

# Python 代码风格规范

## 库导入规范
- 使用绝对路径导入，严禁使用相对路径

## 代码质量与格式化 (Ruff)
- **命令**:
    - 检查并修复 Lint 问题: `uv run ruff check . --fix`
    - 格式化代码: `uv run ruff format .`
- **配置策略**:
    - 优先修改代码以符合规范。
    - 针对框架特性（如 FastAPI/Typer 的 `Depends`/`Option` 默认值），在 `pyproject.toml` 中配置 `extend-per-file-ignores` 忽略 `B008` 等规则，而非在代码中逐行添加 `# noqa`。
    - 脚本文件可忽略导入位置限制 (`E402`)。

## 类型注解
- 使用现代类型注解语法：`X | Y`，而不是 `Optional[X]` 或 `Union[X]`
- 为函数参数和返回值添加类型注解

## 异常处理
- **严禁裸捕获**: 禁止使用 `except:`，必须指定异常类型（如 `except Exception:` 或更具体的异常），防止捕获 `SystemExit` 等系统信号。
- **保留异常链**: 重新抛出异常时，必须使用 `raise ... from e`，保留原始错误堆栈以便调试。
```python
try:
    # 业务逻辑
    ...
except ValueError as e:
    # 记录日志并保留异常链
    logger.exception("数据校验失败")
    raise HTTPException(status_code=400, detail="无效输入") from e
```

## 数据校验
- 使用 Pydantic 进行数据校验
- 定义清晰的数据模型和验证规则



# 日志工具使用规范

## 日志配置
- 日志配置在 logger.py
- 日志适配器在 log_adapter.py
- 应用启动时调用 `setup_logging()` 初始化日志系统

## 日志使用示例
```python
from app.core.log_adapter import logger

logger.info("操作描述")
```

## 日志最佳实践
- 使用结构化日志，通过关键字参数传递变量
- 提供有意义的日志描述
- 在异常处理中使用 `logger.exception()` 记录完整的异常信息
- 避免在日志中记录敏感信息（如密码、token 等）