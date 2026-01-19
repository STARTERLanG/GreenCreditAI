from pathlib import Path
from app.parsers import parse_file

def test_parse_text_file(tmp_path: Path):
    """测试 TXT 文件解析"""
    # 创建临时测试文件
    file = tmp_path / "test.txt"
    file.write_text("Hello GreenCredit", encoding="utf-8")
    
    content = parse_file(file)
    assert content == "Hello GreenCredit"

def test_parse_unsupported_file(tmp_path: Path):
    """测试不支持的文件类型"""
    file = tmp_path / "test.xyz"
    file.touch()
    
    import pytest
    with pytest.raises(ValueError) as excinfo:
        parse_file(file)
    assert "Unsupported file type" in str(excinfo.value)
