"""Uniform random interaction between manager and coder."""

from itertools import count
import random
from simpy import Environment, Store

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


def manager(env, queue):
    while True:
        job = Job()
        print(f"manager creates {job} at {env.now:.2f}")
        yield queue.put(job)
        yield env.timeout(random.uniform(*T_CREATE))


def coder(env, queue):
    while True:
        print(f"coder waits at {env.now:.2f}")
        job = yield queue.get()
        print(f"coder gets {job} at {env.now:.2f}")
        yield env.timeout(job.duration)
        print(f"coder completes {job} at {env.now:.2f}")


if __name__ == "__main__":
    random.seed(RNG_SEED)
    env = Environment()
    queue = Store(env)
    env.process(manager(env, queue))
    env.process(coder(env, queue))
    env.run(until=T_SIM)
