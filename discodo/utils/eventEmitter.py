import asyncio
import traceback
import functools
import collections


class EventEmitter:
    def __init__(self, loop: asyncio.AbstractEventLoop = None):
        self._Events = collections.defaultdict(list)
        self._Any = []

        self.loop = loop or asyncio.get_event_loop()

    def on(self, event: str, func):
        self._Events[event].append(func)
        return self

    def off(self, event: str, func):
        self._Events[event].remove(func)
        return self

    def onAny(self, func):
        self._Any.append(func)
        return self

    def offAny(self, func):
        self._Any.remove(func)
        return self

    async def emit(self, event: str, *args, **kwargs):
        if self._Any:
            for func in self._Any:
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func(event, *args, **kwargs)
                    else:
                        func(event, *args, **kwargs)
                except:
                    traceback.print_exc()

        if not event in self._Events:
            return

        for func in self._Events[event]:
            try:
                if asyncio.iscoroutinefunction(func):
                    await func(*args, **kwargs)
                else:
                    func(*args, **kwargs)
            except:
                traceback.print_exc()

    def dispatch(self, event: str, *args, **kwargs):
        if self._Any:
            for func in self._Any:
                try:
                    if asyncio.iscoroutinefunction(func):
                        self.loop.create_task(func(event, *args, **kwargs))
                    else:
                        self.loop.call_soon_threadsafe(
                            functools.partial(func, event, *args, **kwargs))
                except:
                    traceback.print_exc()

        if not event in self._Events:
            return

        for func in self._Events[event]:
            try:
                if asyncio.iscoroutinefunction(func):
                    self.loop.create_task(func(*args, **kwargs))
                else:
                    self.loop.call_soon_threadsafe(
                        functools.partial(func, *args, **kwargs))
            except:
                traceback.print_exc()

    def event(self, event: str):
        def wrapper(func):
            def decorator(*args, **kwargs):
                self.on(event, func)
            return decorator
        return wrapper

    def once(self, event: str, func):
        def wrapper(*args, **kwargs):
            self.off(event, func)
            return event(*args, **kwargs)

        return self.on(event, wrapper)
