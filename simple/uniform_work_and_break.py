"""Simulate uniform work and break times."""

import random
from simpy import Environment

T_WORK = (10, 50)
T_BREAK = 10
T_MORNING = 4 * 60


def rand_work():
    return random.uniform(*T_WORK)


def worker(env):
    while True:
        print(f"start work at {env.now}")
        yield env.timeout(rand_work())
        print(f"start break at {env.now}")
        yield env.timeout(T_BREAK)


if __name__ == "__main__":
    env = Environment()
    proc = worker(env)
    env.process(proc)
    env.run(until=T_MORNING)
    print(f"done at {env.now}")
