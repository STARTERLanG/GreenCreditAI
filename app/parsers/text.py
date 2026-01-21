from pathlib import Path

from app.parsers.base import FileParser


class TextParser(FileParser):
    def parse(self, file_path: Path) -> str:
        with open(file_path, encoding="utf-8") as f:
            return f.read()
