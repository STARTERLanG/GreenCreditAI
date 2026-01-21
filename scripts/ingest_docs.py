import json
import sys
import time
import requests
import urllib3
from pathlib import Path
from langchain_core.documents import Document
from tqdm import tqdm

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.rag.vector_store import vector_store
from app.core.config import settings
from app.core.logging import logger

# --- 安全的 SSL 修复补丁 (v2.0) ---
# 仅在脚本运行期间禁用 SSL 验证，且不破坏函数签名
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_original_session_request = requests.Session.request

def patched_request(self, method, url, *args, **kwargs):
    # 强制禁用验证，但保留其他所有参数
    kwargs['verify'] = False
    return _original_session_request(self, method, url, *args, **kwargs)

requests.Session.request = patched_request



sys.path.append(str(Path(__file__).resolve().parent.parent))


logger.remove()
logger.add(sys.stderr, level="DEBUG")

def process_json_file(file_path: Path) -> list[Document]:
    """处理 JSON 文件，将每个对象转换为 Document"""
    docs = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            return []
        for idx, item in enumerate(data):
            page_content = "\n".join([f"{k}: {v}" for k, v in item.items()]) if isinstance(item, dict) else str(item)
            docs.append(Document(page_content=page_content, metadata={"source": file_path.name, "seq_num": idx}))
    except Exception as e:
        logger.error(f"Error processing JSON {file_path.name}: {e}")
    return docs

def ingest_knowledge_base():
    kb_dir = settings.KNOWLEDGE_BASE_DIR
    if not kb_dir.exists():
        logger.error(f"Knowledge base directory not found: {kb_dir}")
        return

    files = [f for f in kb_dir.iterdir() if f.suffix in ['.pdf', '.txt', '.md', '.json']]
    if not files:
        logger.warning(f"No documents found in {kb_dir}")
        return

    all_docs = []
    from langchain_community.document_loaders import PyPDFLoader, UnstructuredFileLoader
    
    for file_path in files:
        logger.info(f"Loading document: {file_path.name}")
        try:
            if file_path.suffix == '.json':
                all_docs.extend(process_json_file(file_path))
            elif file_path.suffix == '.pdf':
                all_docs.extend(PyPDFLoader(str(file_path)).load())
            else:
                all_docs.extend(UnstructuredFileLoader(str(file_path)).load())
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")

    if not all_docs:
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks = text_splitter.split_documents(all_docs)

    total_chunks = len(chunks)
    batch_size = 5  # 保持保守的 batch size
    logger.info(f"Total chunks: {total_chunks}. Starting ingestion...")
    
    for i in tqdm(range(0, total_chunks, batch_size), desc="Ingesting"):
        batch = chunks[i : i + batch_size]
        try:
            vector_store.add_documents(batch)
            time.sleep(0.5) 
        except Exception as e:
            logger.error(f"Failed to ingest batch {i // batch_size}: {e}")
            
    logger.info("Ingestion completed successfully!")

if __name__ == "__main__":
    ingest_knowledge_base()