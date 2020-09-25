import asyncio
import collections
import functools
import traceback
from typing import Callable, Coroutine


class EventDispatcher:
    def __init__(self, loop: asyncio.AbstractEventLoop = None) -> None:
        self._Events = collections.defaultdict(list)
        self._listeners = collections.defaultdict(list)
        self._Any = []

        self.loop = loop or asyncio.get_event_loop()

    def on(self, event: str, func: Callable):
        self._Events[event].append(func)
        return self

    def off(self, event: str, func: Callable):
        self._Events[event].remove(func)
        return self

    def onAny(self, func: Callable):
        self._Any.append(func)
        return self

    def offAny(self, func: Callable):
        self._Any.remove(func)
        return self

    def dispatch(self, event_: str, *args, **kwargs) -> None:
        if self._Any:
            for func in self._Any:
                try:
                    if asyncio.iscoroutinefunction(func):
                        self.loop.create_task(func(event_, *args, **kwargs))
                    else:
                        self.loop.call_soon_threadsafe(
                            functools.partial(func, event_, *args, **kwargs)
                        )
                except:
                    traceback.print_exc()

        listeners = self._listeners.get(event_)
        if listeners:
            for Future in listeners:
                if not (Future.done() or Future.cancelled()):
                    Future.set_result(
                        args if len(args) > 1 else (args[0] if args else None)
                    )

                listeners.remove(Future)

            if not listeners:
                self._listeners.pop(event_)

        if not event_ in self._Events:
            return

        for func in self._Events[event_]:
            try:
                if asyncio.iscoroutinefunction(func):
                    self.loop.create_task(func(*args, **kwargs))
                else:
                    self.loop.call_soon_threadsafe(
                        functools.partial(func, *args, **kwargs)
                    )
            except:
                traceback.print_exc()

    def event(self, event: str):
        def wrapper(func):
            self.on(event, func)

        return wrapper

    def once(self, event: str, func: Callable):
        def wrapper(*args, **kwargs):
            self.off(event, func)
            return event(*args, **kwargs)

        return self.on(event, wrapper)

    def wait_for(self, event: str, timeout: float = None) -> Coroutine:
        Future = self.loop.create_future()

        self._listeners[event].append(Future)

        return asyncio.wait_for(Future, timeout)