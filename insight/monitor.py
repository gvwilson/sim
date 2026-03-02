from asimpy import Process
from recorder import Recorder


class QueueMonitor(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)

    async def run(self):
        while True:
            self.sim.log.queue("code", len(self.sim.code_queue._items))
            await self.timeout(self.sim.params.t_queue_monitor)
