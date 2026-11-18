
from typing import Literal,Callable
from voyoagent.utils.subject import Subject

from dataclasses import dataclass


@dataclass
class RunStartEvent:
    type: Literal["run_start"]="run_start"

@dataclass
class ThinkingStartEvent:
    type: Literal["thinking_start"]="thinking_start" #思考流开始

@dataclass
class ThinkingDeltaEvent:
    content: str #流式思考增量
    type: Literal["thinking_delta"]="thinking_delta"

@dataclass
class ThinkingEndEvent:
    type: Literal["thinking_end"]="thinking_end" #思考流结束

@dataclass
class TextStartEvent:
    type: Literal["text_start"]="text_start" #正文流开始

@dataclass
class TextDeltaEvent:
    content: str #流式回答增量
    type: Literal["text_delta"]="text_delta"

@dataclass
class ToolCallEvent:
    call_id: str
    name: str
    arguments: str #原始 JSON 字符串
    type: Literal["tool_call"]="tool_call"

@dataclass
class ToolResultEvent:
    call_id: str
    name:str
    result: str
    type: Literal["tool_result"]="tool_result"

@dataclass
class ToolErrorEvent:
    call_id: str
    name: str
    error: str #错误信息，同时作为 function_call_output 回传给模型
    type: Literal["tool_error"]="tool_error"

@dataclass
class ResponseCompletedEvent:
    type: Literal["response_completed"]="response_completed" #本轮模型响应流结束

@dataclass
class TurnEndEvent:
    type: Literal["turn_end"]="turn_end" #一轮 function_call 回传完成

@dataclass
class DoneEvent:
    content: str #最终全文
    type: Literal["done"]="done"

@dataclass
class ErrorEvent:
    content: str #错误信息
    type: Literal["error"]="error"


type AgentEventType = (
    RunStartEvent | ThinkingStartEvent | ThinkingDeltaEvent | ThinkingEndEvent
    | TextStartEvent | TextDeltaEvent | ResponseCompletedEvent
    | ToolCallEvent | ToolResultEvent | ToolErrorEvent
    | TurnEndEvent | DoneEvent | ErrorEvent
)


class AgentEvent():
    subject:Subject[AgentEventType]

    

    def __init__(self):
        self.subject=Subject[AgentEventType]()

    def write(self,event:AgentEventType):
        self.subject.next(event)

    def subscribe(self,sub:Callable[[AgentEventType],None])->Callable[[],None]:
        return self.subject.subscribe(sub)
