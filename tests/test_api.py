from fastapi.testclient import TestClient


def test_read_root(client: TestClient):
    """测试主页加载"""
    response = client.get("/")
    assert response.status_code == 200
    assert "GreenCredit AI" in response.text


def test_chat_stream(client: TestClient):
    """测试聊天接口连通性 (Mock)"""
    # 这里我们只测试接口是否响应，不真正调用 LLM
    # 实际项目中可以使用 pytest-mock 模拟 LLM 返回
    payload = {"message": "你好"}

    # 只要能发起请求且不报错 500 即可
    # 由于是 StreamingResponse，TestClient 会读取流
    # 我们这里简单测试它返回了 200 OK
    with client.stream("POST", "/api/v1/chat/completions", json=payload) as response:
        assert response.status_code == 200
