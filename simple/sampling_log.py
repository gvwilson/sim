import json
import random
from simpy import Environment
import sys

T_MIN_WORK = 10
T_MAX_WORK = 50
T_BREAK = 10
T_MORNING = 4 * 60
T_LOG = 1

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
        self.state = "idle"
        self.env.process(self.run())

    def run(self):
        while True:
            self.state = "work"
            yield self.env.timeout(t_work())
            self.state = "idle"
            yield self.env.timeout(T_BREAK)


class Logger:
    def __init__(self, env, worker):
        self.env = env
        self.worker = worker
        self.log = []
        self.env.process(self.run())

    def run(self):
        while True:
            self.log.append({"time": self.env.rnow, "state": self.worker.state})
            yield self.env.timeout(T_LOG)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else SEED
    random.seed(seed)
    env = Env()
    log = []
    worker = Worker(env)
    logger = Logger(env, worker)
    env.run(until=T_MORNING)
    json.dump(logger.log, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
