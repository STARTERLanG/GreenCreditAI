import pytest

from app.schemas.chat import ChatRequest
from app.services.workflow_service import workflow_service


@pytest.mark.asyncio
async def test_workflow_stream():
    """测试完整工作流流式输出"""
    request = ChatRequest(message="帮我分析一下华为的绿色表现", session_id="test-session-999", file_hashes=[])

    events = []
    async for event in workflow_service.process_stream(request):
        events.append(event)

    assert len(events) > 0
    # 验证是否包含 think 和 done 事件
    event_types = [e for e in events if "event" in e]
    assert any("think" in e for e in event_types)
    assert any("done" in e for e in event_types)
