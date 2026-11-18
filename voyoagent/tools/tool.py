from typing import TypedDict,Optional
from voyo.utils.json import JSON
from voyoagent.tools.weather_tool import WEATHER_TOOL,WEATHER_FUNCTION
from voyo.model.types import ResponsesFunctionCallOutputItem,ResponsesFunctionCallItem
from voyoagent.tools.tool_types import ToolEntry, ToolDef, Tool_call,Tool_Type
from voyoagent.utils.exception import YoAgentCode,YoAgentException
from voyoagent.agent_base import AgentEvent,ToolCallEvent,ToolResultEvent,ToolErrorEvent
from voyo.utils.unique_id import yo_unique


class AgentTool():
    tool_calls:list[Tool_call]
    tools: list[Tool_Type]
    agent_event:AgentEvent
    def __init__(self,agent_event:AgentEvent):
        self.agent_event=agent_event
        self.tools=[]
        super().__init__()


    def registry_tool(self,tool_entry:ToolEntry):
        tool_def, tool_handler=tool_entry
        name=tool_def.get("name")
        if self.find_tool(name):
            raise YoAgentException(YoAgentCode.COMMON,f"tool 重复注册: {name}")
        tool:Tool_Type= {
            "id": yo_unique.get_uid(),
            "name": name,
            "type": tool_def.get("type"),
            "description": tool_def.get("description"),
            "parameters": tool_def.get("parameters"),
            "tool_handler": tool_handler
        }

        self.tools.append(tool)

    def unregistry_tool(self,tool_name:str):
        idx=next((i for i,t in enumerate(self.tools) if t.get("name")==tool_name),None)
        if idx is not None:
            del self.tools[idx]

    @property
    def wire_tools(self)->list[ToolDef]:
        
        return [
            {"type": t["type"],"name": t["name"],"description": t["description"],"parameters": t["parameters"]}
            for t in self.tools
        ]

    def find_tool(self,tool_name:str):
        return next( (i for i in self.tools if i.get("name") == tool_name), None)

    def parse_tool_from_stream(self,event:dict)->list[ResponsesFunctionCallItem]:
        etype= event.get("type")
        return [ o for o in event.get("response",{}).get("output",{}) if o.get("type") == "function_call" ] if etype == "response.completed" else None
    
    async def check_and_call_tool(self,event:dict)->list[ResponsesFunctionCallOutputItem|ResponsesFunctionCallOutputItem]|None:
        selected_tools=self.parse_tool_from_stream(event)
        if not selected_tools : return

        called_results:list[ResponsesFunctionCallItem|ResponsesFunctionCallOutputItem] = []

        for selected_tool in selected_tools:
            name=selected_tool.get("name")
            tool= self.find_tool(name)
            if not tool: continue
            args=selected_tool.get("arguments")
            tool_handler= tool.get("tool_handler")
            call_id=selected_tool.get("call_id")
            
            #推入事件
            self.agent_event.write(ToolCallEvent(call_id,name,args))
            try:
                result= await (tool_handler(JSON.parse(args)) if args else tool_handler())
            except Exception as e:
                result= f"tool: {name}, 调用失败: {e}"
                self.agent_event.write(ToolErrorEvent(call_id,name,result))
            else:
                self.agent_event.write(ToolResultEvent(call_id,name, result))
            
            called_results.append(selected_tool) #ResponseFunctionCallItem
            called_results.append({
                "type": "function_call_output",
                "call_id": call_id,
                "output": result
            }) #ResponsesFunctionCallOutputItem

        return called_results



