from pathlib import Path
from typing import Protocol

from langchain_core.documents import Document


class FileParser(Protocol):
    """文件解析器接口协议"""

    async def parse(self, file_path: Path) -> list[Document]:
        """
        解析给定路径的文件并返回文档对象列表。
        每个 Document 对象包含 page_content 和 metadata。
        """
        ...
