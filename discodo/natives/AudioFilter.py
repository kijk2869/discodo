import av
import av.filter


class AudioFilter:
    def __init__(self) -> None:
        self.selectAudioStream = None
        self._Filters = {}
        self._FilterChains = []
        self.Graph = None
        self.configured = False

    def setFilters(self, filters: dict) -> None:
        self._Filters = {}
        for filter, value in filters.items():
            self._Filters[filter] = value
        self._Filters["abuffersink"] = None

        self.configure()

    def configure(self) -> None:
        if not self.selectAudioStream:
            return

        self.Graph = av.filter.Graph()
        self._FilterChains = []
        self._FilterChains.append(self.Graph.add_abuffer(self.selectAudioStream))
        for filter, value in self._Filters.items():
            self._FilterChains.append(self.Graph.add(filter, value))
            self._FilterChains[-2].link_to(self._FilterChains[-1])
        self.Graph.configure()

        self.configured = True

    def push(self, Frame: av.AudioFrame) -> None:
        if not self.Graph:
            return

        return self.Graph.push(Frame)

    def pull(self) -> av.AudioFrame:
        if not self.Graph:
            return

        try:
            return self.Graph.pull()
        except av.error.BlockingIOError:
            return None
