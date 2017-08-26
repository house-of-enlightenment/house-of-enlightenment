"""Put all your globals here.

Things like layout and FPS are pretty universal, so
for convenience, just load up a global
"""


# http://www.aleax.it/Python/5ep.html
class Borg(object):
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


#
# Any instance of GlobalState()
# has the same shared state.
# a = GlobalState()
# b = GlobalState()
# a.layout == b.layout
#
class Global(Borg):
    def __init__(self):
        Borg.__init__(self)
        self.layout = None
        self.servers = None
        self.stations = None
        self.fps = None
        self.verbose = False
        self.codes = None
        self.fountains = None


STATE = Global()
