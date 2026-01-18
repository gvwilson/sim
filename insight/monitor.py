class QueueMonitor:
    def __init__(self, sim):
        self.sim = sim
        self.sim.process(self.run())

    def run(self):
        while True:
            self.sim.log.queue("code", len(self.sim.code_queue.items))
            yield self.sim.timeout(self.sim.params.t_queue_monitor)
