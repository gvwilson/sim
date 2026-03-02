from asimpy import Process
from recorder import Recorder


class Actor(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)
        self.post_init()

    def post_init(self):
        pass

    def log(self, state):
        self.sim.log.actor(self.__class__.__name__, self.id, state)

    async def run(self):
        pass
