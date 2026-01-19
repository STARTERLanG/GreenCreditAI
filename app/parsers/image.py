from pathlib import Path
from app.parsers.base import FileParser

class ImageParser(FileParser):
    def parse(self, file_path: Path) -> str:
        # TODO: 集成 OCR (如 Tesseract 或 DashScope VL 模型)
        return "[Image Content Placeholder - OCR not implemented yet]"
