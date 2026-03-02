"""Uniform random interaction between manager and coder."""

from itertools import count
import random
from asimpy import Environment, Process, Queue

RNG_SEED = 98765
T_CREATE = (6, 10)
T_JOB = (8, 12)
T_SIM = 20


class Job:
    _next_id = count()

    def __init__(self):
        self.id = next(Job._next_id)
        self.duration = random.uniform(*T_JOB)

    def __str__(self):
        return f"job-{self.id}"


class Manager(Process):
    def init(self, queue):
        self.queue = queue

    async def run(self):
        while True:
            job = Job()
            print(f"manager creates {job} at {self._env.now:.2f}")
            await self.queue.put(job)
            await self.timeout(random.uniform(*T_CREATE))


class Coder(Process):
    def init(self, queue):
        self.queue = queue

    async def run(self):
        while True:
            print(f"coder waits at {self._env.now:.2f}")
            job = await self.queue.get()
            print(f"coder gets {job} at {self._env.now:.2f}")
            await self.timeout(job.duration)
            print(f"code completes {job} at {self._env.now:.2f}")


if __name__ == "__main__":
    random.seed(RNG_SEED)
    env = Environment()
    queue = Queue(env)
    Manager(env, queue)
    Coder(env, queue)
    env.run(until=T_SIM)
