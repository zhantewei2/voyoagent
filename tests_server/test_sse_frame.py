#SSE 帧格式：data: {json} + 空行，json 含 type 字段
import json

from voyoagent.agent_base import DoneEvent, TextDeltaEvent

from server.service.chat_service import to_sse


def test_to_sse_frame_format():
    frame = to_sse(TextDeltaEvent("你好"))
    assert frame.startswith("data: ")
    assert frame.endswith("\n\n")
    data = json.loads(frame[len("data: "): -2])
    assert data["type"] == "text_delta"
    assert data["content"] == "你好"


def test_to_sse_done_event_has_type():
    data = json.loads(to_sse(DoneEvent("完成"))[len("data: "): -2])
    assert data == {"content": "完成", "type": "done"}
