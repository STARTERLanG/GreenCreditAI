from unittest.mock import patch

import pytest

from app.schemas.chat import ChatRequest
from app.services.workflow_service import workflow_service


@pytest.mark.asyncio
async def test_workflow_stream():
    """测试完整工作流流式输出 (Mocked)"""
    request = ChatRequest(message="test", session_id="test-session-999", file_hashes=[])

    # Mock graph execution to return standard events
    async def mock_stream(*args, **kwargs):
        # chunk mock object with content attribute
        chunk_cls = type("Chunk", (), {"content": "He", "tool_call_chunks": None})
        chunk_cls2 = type("Chunk", (), {"content": "llo", "tool_call_chunks": None})

        yield {
            "event": "on_chain_start",
            "name": "router",
            "data": {},
            "metadata": {"langgraph_node": "router"},
        }
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": chunk_cls()},
            "metadata": {"langgraph_node": "chat"},
        }
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": chunk_cls2()},
            "metadata": {"langgraph_node": "chat"},
        }

    with patch.object(workflow_service, "_graph") as mock_graph:
        mock_graph.astream_events.side_effect = mock_stream

        events = []
        async for event in workflow_service.process_stream(request):
            events.append(event)

        assert len(events) > 0
        # process_stream 将 on_chain_start 转换为 status_update
        # 将 on_chat_model_stream 转换为 answer_delta
        assert any("status_update" in e for e in events)
        assert any("answer_delta" in e for e in events)
        assert any("done" in e for e in events)
