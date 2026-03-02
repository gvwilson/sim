from random import choice, expovariate

from actor import Actor
from jobs import JobInterrupt


class Interrupter(Actor):
    async def run(self):
        while True:
            await self.timeout(self.rand_t_arrival())
            coder = choice(self.sim.coders)
            coder.interrupt(JobInterrupt(self.sim))

    def rand_t_arrival(self):
        return expovariate(1.0 / self.sim.params.t_interrupt_interval)
