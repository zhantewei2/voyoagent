import inspect
from typing import Callable,Awaitable

class Subject[T]:
    subs: list[Callable[[T], None]]
    def __init__(self):

        self.subs=[]

    def next(self,i:T):
        for sub in self.subs:
            sub(i)

    def subscribe(self,fn: callable[T,None])->callable[None]:
        self.subs.append(fn)
        return self.build_unsubscribe(fn)

    def build_unsubscribe(self,fn)->callable[None]:
        def unsubscribe():
            self.subs.remove(fn)

        return unsubscribe

class ASubject[T]:
    subs: list[Callable[[T], Awaitable[None]| None]]
    def __init__(self):
        self.subs=[]

    async def next(self,i:T):
        for sub in self.subs:
            r=sub(i)
            if inspect.isawaitable(r):
                await r

    def subscribe(self,fn: callable[T,None]|callable[T,Awaitable[None]])->callable[None]:
        self.subs.append(fn)
        return self.build_unsubscribe(fn)

    def build_unsubscribe(self,fn)->callable[None]:
        def unsubscribe():
            self.subs.remove(fn)
        return unsubscribe
