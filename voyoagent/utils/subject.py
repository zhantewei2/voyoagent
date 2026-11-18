import inspect
from typing import Callable,Awaitable

class Subject[T]:
    subs: list[Callable[[T], None]]
    def __init__(self):

        self.subs=[]

    def next(self,i:T):
        for sub in self.subs:
            sub(i)

    def subscribe(self,fn: Callable[[T], None])->Callable[[], None]:
        self.subs.append(fn)
        return self.build_unsubscribe(fn)

    def build_unsubscribe(self,fn)->Callable[[], None]:
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

    def subscribe(self,fn: Callable[[T], None]|Callable[[T], Awaitable[None]])->Callable[[], None]:
        self.subs.append(fn)
        return self.build_unsubscribe(fn)

    def build_unsubscribe(self,fn)->Callable[[], None]:
        def unsubscribe():
            self.subs.remove(fn)
        return unsubscribe
