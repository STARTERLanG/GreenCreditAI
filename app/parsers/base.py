from pathlib import Path
from typing import Protocol

class FileParser(Protocol):
    """文件解析器接口协议"""
    def parse(self, file_path: Path) -> str:
        """
        解析给定路径的文件并返回纯文本内容。
        """
        ...
