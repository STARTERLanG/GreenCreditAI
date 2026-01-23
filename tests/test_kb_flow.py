import pytest
from unittest.mock import MagicMock, patch
from fastapi import UploadFile
from io import BytesIO
from app.services.config_service import config_service
from app.models.config import KnowledgeFile
from app.core.db import init_db

# 初始化数据库，创建新表
init_db()

@pytest.mark.asyncio
async def test_kb_ingestion_flow():
    """
    验证知识库文件入库流程：解析 -> 分块 -> 向量化 -> 存库。
    """
    # 1. 模拟上传文件
    content = b"This is a test policy for Green Credit AI Knowledge Base."
    file = UploadFile(filename="test_policy.txt", file=BytesIO(content))
    
    # 2. Mock 依赖
    # Mock document_service.process_file
    mock_process = patch("app.services.config_service.document_service.process_file", 
                         return_value=("This is a test content", "dummy_hash", MagicMock(suffix=".txt", stat=lambda: MagicMock(st_size=100))))
    
    # Mock vector_store.add_documents
    mock_vector = patch("app.services.config_service.vector_store.add_documents")
    
    with mock_process, mock_vector as mock_add:
        # 执行入库
        kb_file = await config_service.ingest_file(file)
        
        # 3. 验证结果
        assert isinstance(kb_file, KnowledgeFile)
        assert kb_file.filename == "test_policy.txt"
        assert kb_file.status == "indexed"
        assert kb_file.chunk_count > 0
        
        # 验证向量库写入是否被调用
        mock_add.assert_called_once()
        print(f"✅ Ingestion successful: {kb_file.chunk_count} chunks created.")

@pytest.mark.asyncio
async def test_kb_list_and_delete():
    """
    验证知识库列表查询和删除逻辑。
    """
    # 1. 查询列表
    files = config_service.list_kb_files()
    initial_count = len(files)
    
    # 2. 模拟删除 (如果列表不为空)
    if initial_count > 0:
        file_id = files[0].id
        success = config_service.delete_kb_file(file_id)
        assert success is True
        
        # 验证数量减少
        files_after = config_service.list_kb_files()
        assert len(files_after) == initial_count - 1
        print("✅ KB file deletion successful.")
    else:
        print("ℹ️ KB is empty, skipping deletion test.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_kb_ingestion_flow())
