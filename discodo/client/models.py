import functools
import logging

log = logging.getLogger("discodo.client.models")


def isInQueue(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self not in self.VoiceClient.Queue:
            raise ValueError("this source is not in queue.")

        return func(self, *args, **kwargs)

    return wrapper


def isNotInQueue(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if self in self.VoiceClient.Queue:
            raise ValueError("this source is already in queue.")

        return func(self, *args, **kwargs)

    return wrapper


class AudioData:
    def __init__(self, VoiceClient, data):
        self.VoiceClient = VoiceClient

        self.data = data
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return f"<AudioData id={self.id} title='{self.title}' duration={self.duration}>"

    def __eq__(self, other):
        if not isinstance(other, (type(self), AudioSource)):
            return False

        return self.id == other.id

    @isNotInQueue
    async def put(self):
        return await self.VoiceClient.putSource(self)

    @isInQueue
    async def getContext(self):
        data = await self.VoiceClient.http.getQueueSource(self.tag)

        return data.get("context")

    @isInQueue
    async def setContext(self, data):
        return await self.VoiceClient.http.setQueueSource(self.tag, {"context": data})

    @isInQueue
    async def moveTo(self, index):
        await self.VoiceClient.http.setQueueSource(self.tag, {"index": index})

        return self

    @isInQueue
    async def seek(self, offset):
        await self.VoiceClient.http.setQueueSource(self.tag, {"start_position": offset})

        return self

    @isInQueue
    async def remove(self):
        await self.VoiceClient.http.removeQueueSource(self.tag)

        return self


class AudioSource:
    def __init__(self, VoiceClient, data):
        self.VoiceClient = VoiceClient

        self.data = data
        for key, value in data.items():
            setattr(self, key, value)

    def __repr__(self) -> str:
        return (
            f"<AudioSource id={self.id} title='{self.title}' duration={self.duration}"
            + (f" position={self.position}" if hasattr(self, "position") else "")
            + f" seekable={self.seekable}>"
        )

    def __eq__(self, other):
        if not isinstance(other, (AudioData, type(self))):
            return False

        return self.id == other.id

    @isInQueue
    async def getContext(self):
        data = await self.VoiceClient.http.getQueueSource(self.tag)

        return data.get("context")

    @isInQueue
    async def setContext(self, data):
        return await self.VoiceClient.http.setQueueSource(self.tag, {"context": data})


ARGUMENT_MAPPING = {"AudioData": AudioData, "AudioSource": AudioSource}


def ensureQueueObjectType(VoiceClient, argument):
    if isinstance(argument, list):
        return list(map(lambda x: ensureQueueObjectType(VoiceClient, x), argument))

    _type = argument.get("_type") if isinstance(argument, dict) else None
    if not _type:
        return argument

    typeObject = ARGUMENT_MAPPING.get(_type)

    if not typeObject:
        log.warning(f"queue object argument type {_type} not found, ignored.")
        return argument

    return typeObject(VoiceClient, argument)


class Queue(list):
    log = logging.getLogger("discodo.client.queue")
    METHOD_REDIRECTION = {"setItem": "__setitem__", "delItem": "__delitem__"}

    def __init__(self, VoiceClient):
        super().__init__()

        self.VoiceClient = VoiceClient
        self.__checkArgumentType = functools.partial(ensureQueueObjectType, VoiceClient)

    def __readonly(self, *args, **kwargs):
        raise RuntimeError("Queue is readonly object.")

    __setitem__ = (
        __delitem__
    ) = pop = remove = append = clear = extend = insert = reverse = __readonly

    def handleGetQueue(self, data):
        entries = list(map(self.__checkArgumentType, data.get("entries", [])))

        if not entries:
            return

        super().clear()
        super().extend(entries)

    def handleQueueEvent(self, data):
        name, args = (
            self.METHOD_REDIRECTION.get(data["name"]) or data["name"],
            list(map(self.__checkArgumentType, data["args"])),
        )

        if not hasattr(super(), name):
            self.log.warning(f"QUEUE_EVENT method {name} not found, ignored.")
            return

        return getattr(super(), name)(*args)
