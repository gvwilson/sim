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


def worker(env, log):
    while True:
        log.append([env.rnow, None])
        yield env.timeout(t_work())
        log[-1][-1] = env.rnow
        yield env.timeout(T_BREAK)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else SEED
    random.seed(seed)
    env = Env()
    log = []
    proc = worker(env, log)
    env.process(proc)
    env.run(until=T_MORNING)
    log[-1][-1] = env.rnow
    json.dump(log, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
