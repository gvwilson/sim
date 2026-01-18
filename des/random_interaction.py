"""Exponential and log-normal interaction between manager and coder."""

from itertools import count
import random
from simpy import Environment, Store


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


def manager(env, queue):
    while True:
        job = Job()
        t_delay = rand_job_arrival()
        print(f"manager creates {job} at {env.now:.2f} waits for {t_delay:.2f}")
        yield queue.put(job)
        yield env.timeout(t_delay)


def coder(env, queue):
    while True:
        print(f"coder waits at {env.now:.2f}")
        job = yield queue.get()
        print(f"coder gets {job} at {env.now:.2f}")
        yield env.timeout(job.duration)
        print(f"code completes {job} at {env.now:.2f}")


if __name__ == "__main__":
    random.seed(RNG_SEED)
    env = Environment()
    queue = Store(env)
    env.process(manager(env, queue))
    env.process(coder(env, queue))
    env.run(until=T_SIM)
