import json
import random
from simpy import Environment
import sys

T_MIN_WORK = 10
T_MAX_WORK = 50
T_BREAK = 10
T_MORNING = 4 * 60

SEED = 12345
PREC = 3


class Env(Environment):
    @property
    def rnow(self):
        return round(self.now, PREC)


def t_work():
    return random.uniform(T_MIN_WORK, T_MAX_WORK)


class Worker:
    def __init__(self, env):
        self.env = env
        self.env.process(self.run())

    def run(self):
        while True:
            print(f"{self.env.rnow} start")
            yield self.env.timeout(t_work())
            print(f"{self.env.rnow} end")
            yield self.env.timeout(T_BREAK)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else SEED
    random.seed(seed)
    env = Env()
    worker = Worker(env)
    env.run(until=T_MORNING)


if __name__ == "__main__":
    main()
