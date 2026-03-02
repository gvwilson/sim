"""Exponential and log-normal interaction between manager and coder."""

from itertools import count
import random
from asimpy import Environment, Process, Queue


RNG_SEED = 98765
T_JOB_INTERVAL = 2.0
T_JOB_MEAN = 0.5
T_JOB_STD = 0.6
T_SIM = 10


def rand_job_arrival():
    return random.expovariate(1.0 / T_JOB_INTERVAL)


def rand_job_duration():
    return random.lognormvariate(T_JOB_MEAN, T_JOB_STD)


class Job:
    _next_id = count()

    def __init__(self):
        self.id = next(Job._next_id)
        self.duration = rand_job_duration()

    def __str__(self):
        return f"job-{self.id}"


class Manager(Process):
    def init(self, queue):
        self.queue = queue

    async def run(self):
        while True:
            job = Job()
            t_delay = rand_job_arrival()
            print(f"manager creates {job} at {self._env.now:.2f} waits for {t_delay:.2f}")
            await self.queue.put(job)
            await self.timeout(t_delay)


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
