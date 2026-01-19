from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from app.parsers.base import FileParser

class PDFParser(FileParser):
    def parse(self, file_path: Path) -> str:
        loader = PyPDFLoader(str(file_path))
        docs = loader.load()
        return "\n\n".join([d.page_content for d in docs])
