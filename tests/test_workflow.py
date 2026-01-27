from unittest.mock import patch

import pytest

from app.schemas.chat import ChatRequest
from app.services.workflow_service import workflow_service


@pytest.mark.asyncio
async def test_workflow_stream():
    """测试完整工作流流式输出 (包含思维链与工具)"""
    request = ChatRequest(message="test", session_id="test-session-999", file_hashes=[])

    # Mock graph execution
    async def mock_stream(*args, **kwargs):
        # chunk mock with content and content_type
        class Chunk:
            def __init__(self, content, content_type="text"):
                self.content = content
                self.content_type = content_type
                self.tool_call_chunks = None

        yield {
            "event": "on_chain_start",
            "name": "policy_enrichment",
            "data": {},
            "metadata": {"langgraph_node": "policy_enrichment"},
        }
        # 推理流 (使用 policy_enrichment 避免被过滤)
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": Chunk("Hmm, I think...", content_type="reasoning")},
            "metadata": {"langgraph_node": "policy_enrichment"},
        }
        # 工具执行
        yield {
            "event": "on_tool_start",
            "name": "search_enterprise_info",
            "run_id": "call_1",
            "data": {"input": {"company_name": "Test"}},
            "metadata": {"langgraph_node": "policy_enrichment"},
        }
        yield {
            "event": "on_tool_end",
            "name": "search_enterprise_info",
            "run_id": "call_1",
            "data": {"output": "Found it."},
            "metadata": {"langgraph_node": "policy_enrichment"},
        }
        # 正交流 (换成 chat 节点，避免被过滤)
        yield {
            "event": "on_chat_model_stream",
            "data": {"chunk": Chunk("Result is positive.")},
            "metadata": {"langgraph_node": "chat"},
        }

    with patch.object(workflow_service, "_graph") as mock_graph:
        # Mock _get_file_content to avoid DB/Network
        with patch.object(workflow_service, "_get_file_content", return_value=None):
            mock_graph.astream_events.side_effect = mock_stream

            events = []
            async for event in workflow_service.process_stream(request):
                import json

                data = json.loads(event.replace("data: ", "").strip())
                events.append(data)

            # 验证事件序列
            event_types = [e["event"] for e in events]
            assert "status_update" in event_types
            assert "thought_delta" in event_types
            assert "tool_start" in event_types
            assert "tool_end" in event_types
            assert "answer_delta" in event_types
            assert "done" in event_types


class AsyncMockIterator:
    def __init__(self, items):
        self.items = items
        self.index = 0

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.index >= len(self.items):
            raise StopAsyncIteration
        result = self.items[self.index]
        self.index += 1
        return result


@pytest.mark.asyncio
async def test_process_stream_filters_json():
    """测试 WorkflowService 能够过滤掉 thought 流中的 JSON 块"""
    from unittest.mock import MagicMock

    from langchain_core.messages import AIMessageChunk

    from app.schemas.chat import ChatRequest
    from app.services.workflow_service import WorkflowService

    mock_graph = MagicMock()

    # 模拟一个产生 JSON 块的内部节点事件
    mock_events = [
        {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "extractor"},
            "data": {"chunk": AIMessageChunk(content='{"key": "val"}')},
        },
        {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "extractor"},
            "data": {"chunk": AIMessageChunk(content="PROJECT_AUDIT{...}")},
        },
        {
            "event": "on_chat_model_stream",
            "metadata": {"langgraph_node": "extractor"},
            "data": {"chunk": AIMessageChunk(content="正在思考...")},  # 合法思考文本
        },
    ]

    mock_graph.astream_events.return_value = AsyncMockIterator(mock_events)

    ws = WorkflowService()
    ws._graph = mock_graph

    # Mock _get_file_content to avoid DB
    with patch.object(ws, "_get_file_content", return_value=None):
        req = ChatRequest(message="test", session_id="s1", file_hashes=[])
        events = []
        async for event in ws.process_stream(req):
            events.append(event)

    # 验证产生了一个 thought_delta (正在思考...)
    # 而 JSON 块和 PROJECT_ 块被过滤了
    thought_events = [e for e in events if "thought_delta" in e]
    assert len(thought_events) == 1
    assert "正在思考" in thought_events[0]
