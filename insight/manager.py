from random import expovariate

from actor import Actor
from jobs import JobRegular


class Manager(Actor):
    async def run(self):
        while True:
            job = JobRegular(self.sim)
            await self.sim.code_queue.put(job)
            for coder in self.sim.coders:
                coder.notify_work()
            await self.timeout(self.rand_t_arrival())

    def rand_t_arrival(self):
        return expovariate(1.0 / self.sim.params.t_code_interval)
