from pathlib import Path

import pytest
from langchain_core.documents import Document

from app.parsers import parse_file


@pytest.mark.asyncio
async def test_parse_text_file(tmp_path: Path):
    """测试 TXT 文件解析"""
    # 创建临时测试文件
    file = tmp_path / "test.txt"
    file.write_text("Hello GreenCredit", encoding="utf-8")

    docs = await parse_file(file)
    assert isinstance(docs, list)
    assert len(docs) == 1
    assert isinstance(docs[0], Document)
    assert docs[0].page_content == "Hello GreenCredit"
    assert docs[0].metadata["type"] == "text"


@pytest.mark.asyncio
async def test_parse_unsupported_file(tmp_path: Path):
    """测试不支持的文件类型"""
    file = tmp_path / "test.xyz"
    file.touch()

    with pytest.raises(ValueError) as excinfo:
        await parse_file(file)
    assert "Unsupported file type" in str(excinfo.value)
