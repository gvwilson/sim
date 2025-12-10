import random
from simpy import Environment

T_MIN_WORK = 10
T_MAX_WORK = 50
T_BREAK = 10
T_MORNING = 4 * 60


def t_work():
    return random.uniform(T_MIN_WORK, T_MAX_WORK)


def worker(env):
    while True:
        print(f"start work at {env.now}")
        yield env.timeout(t_work())
        print(f"start break at {env.now}")
        yield env.timeout(T_BREAK)


if __name__ == "__main__":
    env = Environment()
    proc = worker(env)
    env.process(proc)
    env.run(until=T_MORNING)
    print(f"done at {env.now}")
