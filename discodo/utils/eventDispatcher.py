import asyncio
import collections
import functools
import traceback
from typing import Callable


class EventDispatcher:
    r"""Represents an event dispatcher similar to EventEmitter_

    .. _EventEmitter: https://nodejs.org/api/events.html#events_class_eventemitter

    :var Optional[asyncio.AbstractEventLoop] loop: The event loop that the dispatcher uses for operation, defaults to :py:meth:`asyncio.get_event_loop`"""

    def __init__(self, loop: asyncio.AbstractEventLoop = None) -> None:
        self._Events = collections.defaultdict(list)
        self._listeners = collections.defaultdict(list)
        self._Any = []

        self.loop = loop or asyncio.get_event_loop()

    def on(self, event: str, func: Callable):
        """Adds the ``func`` function to the end of the listeners list of the ``event``

        :param str event: The event name to listen to.
        :param Callable func: The function to call when event dispatching.

        :rtype: discodo.EventDispatcher"""

        self._Events[event].append(func)
        return self

    def off(self, event: str, func: Callable):
        """Remove the ``func`` function from the listeners list of the ``event``

        :param str event: The event name to remove from.
        :param Callable func: The function to remove from the list.

        :rtype: discodo.EventDispatcher"""

        self._Events[event].remove(func)
        return self

    def onAny(self, func: Callable):
        """Adds the ``func`` function to the end of the listeners list

        :param Callable func: The function to call when event dispatching.

        :rtype: discodo.EventDispatcher"""

        self._Any.append(func)
        return self

    def offAny(self, func: Callable):
        """Remove the ``func`` function from the listeners list

        :param Callable func: The function to remove from the list.

        :rtype: discodo.EventDispatcher"""

        self._Any.remove(func)
        return self

    def dispatch(self, event_: str, *args, **kwargs) -> None:
        r"""Call the listeners which is matched with event name.

        :param str event_: The event name to dispatch.
        :param \*args: An argument list of data to dispatch with.
        :param \*kwargs: A keyword argument list of data to dispatch with."""

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
        """A decorator that registers an event to listen to.

        :param str event: The event name to listen to."""

        def wrapper(func):
            self.on(event, func)

        return wrapper

    async def wait_for(
        self, event: str, condition: Callable = None, timeout: float = None
    ):
        """Waits for an event that is matching with ``condition`` to be dispatched for ``timeout``

        :param str event: The event name to wait for
        :param Optional[Callable] condition: A predicate to check what to wait for. this function must return ``bool``
        :param Optional[float] timeout: The number of seconds to wait.

        :raises asyncio.TimeoutError: The timeout is provided and it was reached.

        :rtype: Any"""

        Future = self.loop.create_future()

        if not condition:
            condition = lambda *_: True

        self._listeners[event].append((Future, condition))

        return await asyncio.wait_for(Future, timeout)
