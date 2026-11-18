import inspect
from typing import Callable, Optional, Awaitable

from voyoagent.utils.subject import ASubject

#钩子回调，支持同步函数或 async 函数
Handler=Callable[..., Optional[Awaitable[None]]]


class Agent_Hook():
    #agent 生命周期钩子，注册到 Voyo_Agent 后由其在对应节点触发
    on_agent_init:ASubject[None] #agent 初始化完成
    on_user_input:ASubject[str] #每次用户发起对话，参数: content
    on_dialog_end:ASubject[None]   #每次对话结束

    def __init__(self):
        self.on_agent_init=ASubject[None]()
        self.on_user_input=ASubject[str]()
        self.on_dialog_end=ASubject[None]()


    async def emit_agent_init(self):
        await self.on_agent_init.next(None)
    async def emit_user_input(self,content:str):
        await self.on_user_input.next(content)
    async def emit_dialog_end(self):
        await self.on_dialog_end.next(None)
