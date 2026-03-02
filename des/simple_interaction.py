"""Simple interaction between manager and coder."""

from itertools import count
from asimpy import Environment, Process, Queue

T_CREATE = 6
T_JOB = 8
T_SIM = 20


class Job:
    _next_id = count()

    def __init__(self):
        self.id = next(Job._next_id)
        self.duration = T_JOB

    def __str__(self):
        return f"job-{self.id}"


class Manager(Process):
    def init(self, queue):
        self.queue = queue

    async def run(self):
        while True:
            job = Job()
            print(f"manager creates {job} at {self._env.now}")
            await self.queue.put(job)
            await self.timeout(T_CREATE)


class Coder(Process):
    def init(self, queue):
        self.queue = queue

    async def run(self):
        while True:
            print(f"coder waits at {self._env.now}")
            job = await self.queue.get()
            print(f"coder gets {job} at {self._env.now}")
            await self.timeout(job.duration)
            print(f"code completes {job} at {self._env.now}")


if __name__ == "__main__":
    env = Environment()
    queue = Queue(env)
    Manager(env, queue)
    Coder(env, queue)
    env.run(until=T_SIM)
