import asyncio
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document

from app.parsers.base import FileParser


class PDFParser(FileParser):
    async def parse(self, file_path: Path) -> list[Document]:
        loader = PyPDFLoader(str(file_path))
        # 使用 to_thread 避免在解析大文件时阻塞事件循环
        return await asyncio.to_thread(loader.load)
