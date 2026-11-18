from voyoagent.tools.tool_types import ToolDef


WEATHER_TOOL:ToolDef = {
    "type": "function",
    "name": "get_weather",
    "description": "查询指定城市当前天气",
    "parameters": {
        "type": "object",
        "properties": {"city": {"type": "string", "description": "城市名，如：北京"}},
        "required": ["city"],
    },
}

async def WEATHER_FUNCTION(city:str=None):
    return f"{city}的天气为 多雨转阴， 21摄氏度"


WEATHER_TOOL_ENTRY=(WEATHER_TOOL,WEATHER_FUNCTION)
