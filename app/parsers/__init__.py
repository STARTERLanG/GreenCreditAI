from pathlib import Path

from langchain_core.documents import Document

from app.core.logging import logger
from app.parsers.image import ImageParser
from app.parsers.office import ExcelParser, PPTParser, WordParser
from app.parsers.pdf import PDFParser
from app.parsers.text import TextParser

# 注册解析器映射
PARSER_REGISTRY = {
    ".pdf": PDFParser(),
    ".xlsx": ExcelParser(),
    ".xls": ExcelParser(),
    ".docx": WordParser(),
    ".doc": WordParser(),
    ".pptx": PPTParser(),
    ".ppt": PPTParser(),
    ".txt": TextParser(),
    ".md": TextParser(),
    ".json": TextParser(),
    ".png": ImageParser(),
    ".jpg": ImageParser(),
    ".jpeg": ImageParser(),
}


async def parse_file(file_path: Path) -> list[Document]:
    """
    通用文件解析入口。
    根据文件后缀分发给具体的 Parser 实现。
    """
    suffix = file_path.suffix.lower()
    parser = PARSER_REGISTRY.get(suffix)

    if not parser:
        raise ValueError(f"Unsupported file type: {suffix}")

    logger.info(f"Parsing {file_path.name} using {parser.__class__.__name__}...")
    try:
        return await parser.parse(file_path)
    except Exception as e:
        logger.error(f"Failed to parse {file_path}: {e}")
        raise e
