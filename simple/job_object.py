"""Represent jobs as objects that record data."""

from itertools import count
import json
import random
from simpy import Environment, Store
import sys

T_SIM = 100
T_JOB_ARRIVAL = (10, 30)
T_WORK = (10, 50)
SEED = 12345
PREC = 3


def rt(env):
    return round(env.now, PREC)


def rand_job_arrival():
    return random.uniform(*T_JOB_ARRIVAL)


def rand_work():
    return random.uniform(*T_WORK)


class Job:
    _id = count()
    _log = []

    def __init__(self, env):
        self.env = env
        self.id = next(Job._id)
        self.log("created")

    def log(self, message):
        Job._log.append({"time": rt(self.env), "id": self.id, "event": message})


def manager(env, queue):
    while True:
        yield queue.put(Job(env))
        yield env.timeout(rand_job_arrival())


def programmer(env, queue):
    while True:
        job = yield queue.get()
        job.log("start")
        yield env.timeout(rand_work())
        job.log("end")


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else SEED
    t_sim = int(sys.argv[2]) if len(sys.argv) > 2 else T_SIM
    random.seed(seed)

    env = Environment()
    queue = Store(env)

    env.process(manager(env, queue))
    env.process(programmer(env, queue))
    env.run(until=t_sim)

    params = {
        "seed": seed,
        "t_sim": t_sim,
        "t_job_arrival": T_JOB_ARRIVAL,
        "t_work": T_WORK,
    }
    result = {
        "params": params,
        "tasks": Job._log,
    }
    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
