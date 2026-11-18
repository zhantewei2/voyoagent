from datetime import datetime

from voyoagent.agent import Voyo_Agent
from voyoagent.tools import (
    WEATHER_TOOL_ENTRY, READ_FILE_ENTRY, WRITE_FILE_ENTRY,
    LIST_DIR_ENTRY, RUN_SHELL_ENTRY, REPLACE_FILE_ENTRY,
)
from voyoagent.utils.common_utils import os_family
TIME_FRAGMENT_ID="current_time"
PLATFORM_FRAGMENT_ID="platform"

#高阶 agent 内置工具，实例化即注册，外部无需手动注册（load_skill 由 Agent_Skill 注册）
BUILTIN_TOOLS=[WEATHER_TOOL_ENTRY, READ_FILE_ENTRY, WRITE_FILE_ENTRY, LIST_DIR_ENTRY, RUN_SHELL_ENTRY, REPLACE_FILE_ENTRY]


class Yo_Agent(Voyo_Agent):
    def __init__(self,auto_registry_tool:bool=True,**args):
        
        super().__init__(**args)

        if auto_registry_tool:
            for entry in BUILTIN_TOOLS:
                self.registry_tool(entry)


    async def init(self):
        self.sub_hook()
        await super().init()


    def sub_hook(self):
        #super.init() 之前订阅，保证 on_agent_init 触发时钩子已就位
        self.agent_hook.on_agent_init.subscribe(self.init_fragment)
        self.agent_hook.on_user_input.subscribe(self.refresh_time_fragment)


    async def init_fragment(self,_:None):
        #初始化时一次性注入全部 fragment；平台信息静态，仅时间需按轮刷新
        self.agent_prompt.append_fragment_prompt(TIME_FRAGMENT_ID,self.get_time_fragment())
        self.agent_prompt.append_fragment_prompt(PLATFORM_FRAGMENT_ID,self.get_platform_fragment())


    async def refresh_time_fragment(self,content:str):
        self.agent_prompt.replace_fragment_prompt(TIME_FRAGMENT_ID,self.get_time_fragment())

    def get_platform_fragment(self)->str:
        return f"Current system: {os_family()}. Keep the OS in mind when running shell commands or operating on files."

    def get_time_fragment(self)->str:
        now=datetime.now().astimezone()
        return f"当前时间: {now:%Y-%m-%d}，时区: {now:%z}"
