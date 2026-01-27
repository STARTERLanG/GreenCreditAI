import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document

from app.services.document_service import document_service


@pytest.mark.asyncio
async def test_document_processing_flow(tmp_path: Path):
    """测试文件上传、哈希、解析、存储全流程"""
    import io

    content_bytes = b"dummy excel content"

    # Mock UploadFile
    mock_upload = MagicMock()
    mock_upload.filename = "test.xlsx"
    mock_upload.file = io.BytesIO(content_bytes)

    # Mock parse_file to return high-fidelity docs
    mock_docs = [
        Document(page_content="Row 1", metadata={"sheet": "S1", "row": 1, "type": "excel"}),
        Document(page_content="Row 2", metadata={"sheet": "S1", "row": 2, "type": "excel"}),
    ]

    with patch("app.services.document_service.parse_file", return_value=mock_docs) as mock_parse:
        # Mock Session and select
        with patch("app.services.document_service.Session") as mock_session:
            session_inst = mock_session.return_value.__enter__.return_value
            session_inst.get.return_value = None  # No cache hit

            result = await document_service.process_file(mock_upload)

            assert result["status"] == "success"
            assert "file_hash" in result

            # 验证解析后的 JSON 序列化
            # session_inst.add(new_cache) 被调用
            new_cache = session_inst.add.call_args[0][0]
            content_data = json.loads(new_cache.content)
            assert len(content_data) == 2
            assert content_data[0]["metadata"]["sheet"] == "S1"
            assert content_data[0]["page_content"] == "Row 1"


@pytest.mark.asyncio
async def test_index_document_task_reconstruction():
    """测试从 JSON 还原 Document 对象并索引"""
    file_hash = "fake_hash"
    mock_content = json.dumps([{"page_content": "Hello", "metadata": {"page": 1, "type": "pdf"}}])

    with patch("app.services.document_service.Session") as mock_session:
        session_inst = mock_session.return_value.__enter__.return_value

        mock_record = MagicMock()
        mock_record.content = mock_content
        mock_record.filename = "test.pdf"
        session_inst.get.return_value = mock_record

        with patch("app.services.document_service.vector_store") as mock_vector:
            await document_service.index_document_task(file_hash)

            # 验证 add_documents 被调用
            added_docs = mock_vector.add_documents.call_args[0][0]
            assert len(added_docs) > 0
            assert added_docs[0].metadata["page"] == 1
            assert added_docs[0].metadata["file_hash"] == file_hash
