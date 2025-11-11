"""Pool of developers with tasks as processes."""

import random
import simpy
from util import TaskUniform, DeveloperUniform


NUM_DEVELOPERS = 3
SIMULATION_DURATION = 20
TASK_ARRIVAL_RATE = 3


def simulate_task(env, developers, task):
    """Simulate a task flowing through the system."""

    print(f"{env.now:.2f}: {task} arrives")
    request_start = env.now
    developer = yield developers.get()
    actual_duration = task._duration / developer._speed
    delay = env.now - request_start
    print(f"{env.now:.2f}: {task} starts on {developer} after delay {delay:.2f} duration {actual_duration:.2f}")
    yield env.timeout(actual_duration)
    print(f"{env.now:.2f}: {task} finishes")
    yield developers.put(developer)


def generate_tasks(env, developers):
    """Generates tasks at random intervals."""

    while True:
        yield env.timeout(random.expovariate(1.0 / TASK_ARRIVAL_RATE))
        env.process(simulate_task(env, developers, TaskUniform()))


def main(args):
    """Run simulation."""

    env = simpy.Environment()
    developers = simpy.Store(env, capacity=NUM_DEVELOPERS)
    developers.items = [DeveloperUniform() for _ in range(NUM_DEVELOPERS)]
    env.process(generate_tasks(env, developers))
    env.run(until=SIMULATION_DURATION)
