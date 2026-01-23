from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.strategies.base import SplittingStrategy

class GeneralRecursiveStrategy(SplittingStrategy):
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 100):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def split(self, text: str, metadata: dict) -> list[Document]:
        chunks = self.splitter.split_text(text)
        return [
            Document(page_content=chunk, metadata=metadata)
            for chunk in chunks
        ]
