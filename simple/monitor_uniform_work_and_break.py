"""Monitor simulation of uniformly distributed work."""

import json
import random
from simpy import Environment
import sys

T_WORK = (10, 50)
T_BREAK = 10
T_MORNING = 4 * 60

SEED = 12345
PREC = 3


def rand_work():
    return random.uniform(*T_WORK)


def worker(env, log):
    while True:
        log.append({"event": "start", "time": round(env.now, PREC)})
        yield env.timeout(rand_work())
        log.append({"event": "end", "time": round(env.now, PREC)})
        yield env.timeout(T_BREAK)


def main():
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else SEED
    random.seed(seed)
    env = Environment()
    log = []
    proc = worker(env, log)
    env.process(proc)
    env.run(until=T_MORNING)
    json.dump(log, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
