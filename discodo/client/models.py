import functools
import logging
import time

from ..enums import PlayerState

log = logging.getLogger("discodo.client.models")


def isInQueue(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self not in self.VoiceClient.Queue:
            raise ValueError("this source is not in queue.")

        return await func(self, *args, **kwargs)

    return wrapper


def isNotInQueue(func):
    @functools.wraps(func)
    async def wrapper(self, *args, **kwargs):
        if self in self.VoiceClient.Queue:
            raise ValueError("this source is already in queue.")

        return await func(self, *args, **kwargs)

    return wrapper


class AudioData:
    r"""Object with playback information

    .. container:: operations

        .. describe:: x == y

            Checks if two AudioSources are equal.

        .. describe:: x != y

            Checks if two AudioSources are not equal.

    :var str tag: The tag of the object
    :var str id: The id of the source
    :var Optional[str] title: The title of the source
    :var Optional[str] webpage_url: The webpage url of the source
    :var Optional[str] thumbnail: The thumbnail url of the source
    :var Optional[str] url: The stream url of the source
    :var Optional[int] duration: The duration of the source
    :var bool is_live: Whether the source is live stream or not
    :var Optional[str] uploader: The uploader of the source
    :var Optional[str] description: The description of the source
    :var dict subtitles: The description of the source
    :var dict chapters: The description of the source
    :var bool related: Whether this source is added by autoplay
    :var dict context: The context of the object
    :var float start_position: The start position of the source"""

    def __init__(self, VoiceClient, data):
        self.VoiceClient = VoiceClient

        self.data = data

    def __getattr__(self, key):
        return self.data.get(key)

    def __getitem__(self, key):
        return self.data.get(key)

    def get(self, *args, **kwargs):
        return self.data.get(*args, **kwargs)

    def toDict(self):
        return self.data

    def __repr__(self) -> str:
        return f"<AudioData id={self.id} title='{self.title}' duration={self.duration}>"

    def __eq__(self, other):
        if not isinstance(other, (type(self), AudioSource)):
            return False

        return self.tag == other.tag

    def __ne__(self, other):
        if not isinstance(other, (type(self), AudioSource)):
            return False

        return self.tag == other.tag

    @isNotInQueue
    async def put(self):
        r"""Put the source into the queue.

        :raise ValueError: The source is already in the queue.

        :rtype: AudioData"""

        return await self.VoiceClient.putSource(self)

    @isInQueue
    async def getContext(self):
        r"""Get the context from the node.

        :rtype: dict"""

        data = await self.VoiceClient.http.getQueueSource(self.tag)
        self.context = data.get("context", {})

        return self.context

    @isInQueue
    async def setContext(self, data):
        r"""Set the context to the node.

        :param dict data: The context to set.

        :rtype: dict"""

        data = await self.VoiceClient.http.setQueueSource(self.tag, {"context": data})
        self.context = data.get("context", {})

        return self.context

    @isInQueue
    async def moveTo(self, index):
        r"""Move this source to index in the queue.

        :param int index: The index to move to

        :rtype: AudioData"""

        await self.VoiceClient.http.setQueueSource(self.tag, {"index": index})

        return self

    @isInQueue
    async def seek(self, offset):
        r"""Seek this source to offset.

        :param float offset: The position to start playing

        :rtype: AudioData"""

        await self.VoiceClient.http.setQueueSource(self.tag, {"start_position": offset})

        return self

    @isInQueue
    async def remove(self):
        r"""Remove this source from the queue.

        :rtype: AudioData"""

        await self.VoiceClient.http.removeQueueSource(self.tag)

        return self


class AudioSource:
    r"""Object with playback information that is loaded

    .. container:: operations

        .. describe:: x == y

            Checks if two AudioSources are equal.

        .. describe:: x != y

            Checks if two AudioSources are not equal.

    :var str tag: The tag of the object
    :var str id: The id of the source
    :var Optional[str] title: The title of the source
    :var Optional[str] webpage_url: The webpage url of the source
    :var Optional[str] thumbnail: The thumbnail url of the source
    :var Optional[str] url: The stream url of the source
    :var float duration: The duration of the source
    :var bool is_live: Whether the source is live stream or not
    :var Optional[str] uploader: The uploader of the source
    :var Optional[str] description: The description of the source
    :var dict subtitles: The description of the source
    :var dict chapters: The description of the source
    :var bool related: Whether this source is added by autoplay
    :var dict context: The context of the object
    :var float start_position: The start position of the source
    :var bool seekable: Whether the source is seekable or not
    :var Optional[float] position: The current position of the source"""

    def __init__(self, VoiceClient, data):
        self.VoiceClient = VoiceClient

        self.data = data

    def __getattr__(self, key):
        return self.data.get(key)

    def __getitem__(self, key):
        if key == "position":
            return self.position

        return self.data.get(key)

    def get(self, key, *args, **kwargs):
        if key == "position":
            return self.position

        return self.data.get(key, *args, **kwargs)

    def toDict(self):
        return self.data

    @property
    def position(self):
        if not self.data["position"]:
            return

        if self.VoiceClient.state != PlayerState.PAUSED:
            self.data["position"] = round(
                self.data["position"]
                + (time.time() - self.as_of if "as_of" in self.data else 0),
                2,
            )
            self.as_of = time.time()

        return self.data["position"]

    def __repr__(self) -> str:
        return (
            f"<AudioSource id={self.id} title='{self.title}' duration={self.duration}"
            + (f" position={self.position}" if hasattr(self, "position") else "")
            + f" seekable={self.seekable}>"
        )

    def __eq__(self, other):
        if not isinstance(other, (AudioData, type(self))):
            return False

        return self.tag == other.tag

    def __ne__(self, other):
        if not isinstance(other, (AudioData, type(self))):
            return False

        return self.tag != other.tag

    async def getContext(self):
        r"""Get the context from the node.

        :rtype: dict"""

        if self in self.VoiceClient.Queue:
            data = await self.VoiceClient.http.getQueueSource(self.tag)
        else:
            data = await self.VoiceClient.http.getCurrent()

        self.context = data.get("context", {})

        return self.context

    async def setContext(self, data):
        r"""Set the context to the node.

        :param dict data: The context to set.

        :rtype: dict"""

        if self in self.VoiceClient.Queue:
            data = await self.VoiceClient.http.setQueueSource(
                self.tag, {"context": data}
            )
        else:
            data = await self.VoiceClient.http.setCurrent({"context": data})

        self.context = data.get("context", {})

        return self.context


ARGUMENT_MAPPING = {"AudioData": AudioData, "AudioSource": AudioSource}


def ensureQueueObjectType(VoiceClient, argument):
    if isinstance(argument, list):
        return list(map(lambda x: ensureQueueObjectType(VoiceClient, x), argument))

    _type = argument.get("_type") if isinstance(argument, dict) else None

    typeObject = ARGUMENT_MAPPING.get(_type)

    if not _type or not typeObject:
        if isinstance(argument, dict):
            return dict(
                list(
                    map(
                        lambda x: (x[0], ensureQueueObjectType(VoiceClient, x[1])),
                        argument.items(),
                    )
                )
            )

        return argument

    return typeObject(VoiceClient, argument)


class Queue(list):
    log = logging.getLogger("discodo.client.queue")
    METHOD_REDIRECTION = {"setItem": "__setitem__", "delItem": "__delitem__"}

    def __init__(self, VoiceClient):
        super().__init__()

        self.VoiceClient = VoiceClient
        self.__checkArgumentType = functools.partial(ensureQueueObjectType, VoiceClient)

    @staticmethod
    def __readonly(*args, **kwargs):
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
