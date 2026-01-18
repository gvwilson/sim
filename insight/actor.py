from recorder import Recorder


class Actor(Recorder):
    def __init__(self, sim):
        super().__init__(sim)
        self.post_init()
        self.proc = self.sim.process(self.run())

    def post_init(self):
        pass

    def log(self, state):
        self.sim.log.actor(self.__class__.__name__, self.id, state)
