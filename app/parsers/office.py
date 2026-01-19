from pathlib import Path
from langchain_community.document_loaders import UnstructuredExcelLoader
from docx import Document as DocxDocument
from app.parsers.base import FileParser

class ExcelParser(FileParser):
    def parse(self, file_path: Path) -> str:
        loader = UnstructuredExcelLoader(str(file_path))
        docs = loader.load()
        return "\n\n".join([d.page_content for d in docs])

class WordParser(FileParser):
    def parse(self, file_path: Path) -> str:
        doc = DocxDocument(file_path)
        full_text = []
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)
        return "\n".join(full_text)
