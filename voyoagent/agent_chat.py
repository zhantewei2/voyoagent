from voyoagent.tools.tool import AgentTool
from voyoagent.agent_base import AgentEvent,ThinkingDeltaEvent,ThinkingEndEvent,ThinkingStartEvent,ResponseCompletedEvent,TextDeltaEvent,TextStartEvent

from typing import AsyncIterator
from voyo.model.types import OpenAiResponsesMsg,ResponsesFunctionCallOutputItem,ResponsesFunctionCallItem
from voyo.model import OpenAiResponsesClient,ModelUsage
from voyoagent.agent_hook import Agent_Hook
from voyoagent.prompt import AgentPrompt


class AgentChat(AgentTool):
    client: OpenAiResponsesClient
    history: list[OpenAiResponsesMsg]
    agent_hook: Agent_Hook
    agent_prompt: AgentPrompt

    def __init__(self,agent_event:AgentEvent):
        self.history=[]
        self.agent_hook=Agent_Hook()
        super().__init__(agent_event)

    async def achat(self,content:str=None)->AsyncIterator[str]|None:
        if content:
            msg:OpenAiResponsesMsg={"role": "user", "content": content}
            self.history.append(msg)
        
        usage:ModelUsage=ModelUsage()

        r=await self.client.achat(
            model=self.model,
            effort=self.effort,
            stream=True,
            messages= self.agent_prompt.get_unified_message() + self.history,
            usage=usage,
            extra_body={
                "tools": self.wire_tools or [],
            }
        )

        thinking_result=""
        text_result= "" 
        thinking=False
        async for i in r:
            event=OpenAiResponsesClient._parse_event(i)
            if not event:
                continue
            
            etype= event.get("type","")

            text= event.get("delta") if etype == "response.output_text.delta" else ""
            thinking_text= event.get("delta") if etype in ("response.reasoning_text.delta", "response.reasoning_summary_text.delta") else ""

            event= OpenAiResponsesClient._parse_event(i)

            if thinking_text:
                if not thinking:
                    thinking=True
                    self.agent_event.write(ThinkingStartEvent())
                self.agent_event.write(ThinkingDeltaEvent(thinking_text))
                thinking_result+=thinking_text

            if text:
                if thinking:
                    self.agent_event.write(ThinkingEndEvent())
                    thinking=False
                if not text_result:
                    self.agent_event.write(TextStartEvent())
                self.agent_event.write(TextDeltaEvent(text))
                text_result+=text

            self.next_call_tools= await self.check_and_call_tool(event)
            
        self.agent_event.write(ResponseCompletedEvent())
        if thinking_result: 
            self.history.append({
                "type": "reasoning",
                "content": [{
                    "type": "reasoning_text",
                    "text": thinking_result
                }]
            })

        if text_result:
            self.history.append(
                {"role": "assistant", "content": text_result}
            )

        return None
