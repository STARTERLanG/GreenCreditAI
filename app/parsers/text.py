import asyncio
from pathlib import Path

from langchain_core.documents import Document

from app.parsers.base import FileParser


class TextParser(FileParser):
    async def parse(self, file_path: Path) -> list[Document]:
        def _read_text():
            with open(file_path, encoding="utf-8") as f:
                return f.read()

        content = await asyncio.to_thread(_read_text)
        return [Document(page_content=content, metadata={"source": str(file_path), "type": "text"})]
