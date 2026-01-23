from abc import ABC, abstractmethod
from langchain_core.documents import Document

class SplittingStrategy(ABC):
    @abstractmethod
    def split(self, text: str, metadata: dict) -> list[Document]:
        """
        根据特定逻辑将文本切分为文档片段
        """
        pass
