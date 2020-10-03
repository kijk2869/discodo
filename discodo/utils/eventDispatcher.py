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
            for (Future, condition) in listeners:
                if not (Future.done() or Future.cancelled()):
                    try:
                        result = condition(*args, **kwargs)
                    except Exception as exception:
                        Future.set_exception(exception)
                        result = True
                    else:
                        if result:
                            Future.set_result(
                                args if len(args) > 1 else (args[0] if args else None)
                            )

                    if result:
                        listeners.remove((Future, condition))

            if not listeners:
                self._listeners.pop(event_)

        if not event_ in self._Events:
            return

        for func in self._Events[event_]:
            try:
                if asyncio.iscoroutinefunction(func):
                    asyncio.run_coroutine_threadsafe(func(*args, **kwargs), self.loop)
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

    def wait_for(
        self, event: str, condition: Callable = None, timeout: float = None
    ) -> Coroutine:
        Future = self.loop.create_future()

        if not condition:
            condition = lambda *_: True

        self._listeners[event].append((Future, condition))

        return asyncio.wait_for(Future, timeout)
