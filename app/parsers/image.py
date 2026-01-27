from pathlib import Path

from langchain_core.documents import Document

from app.parsers.base import FileParser


class ImageParser(FileParser):
    async def parse(self, file_path: Path) -> list[Document]:
        # TODO: 集成 OCR (如 Tesseract 或 DashScope VL 模型)
        # 目前先通过 to_thread 返回占位符以保持接口一致性
        return [
            Document(
                page_content="[Image Content Placeholder - OCR not implemented yet]",
                metadata={"source": str(file_path), "page": 1, "type": "image"},
            )
        ]
