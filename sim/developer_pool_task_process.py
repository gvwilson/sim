"""Pool of developers with tasks as processes."""

import random
import simpy
from util import TaskUniform


NUM_DEVELOPERS = 3
SIMULATION_DURATION = 20
TASK_ARRIVAL_RATE = 3


def simulate_task(env, developers, task):
    """Simulate a task flowing through the system."""

    print(f"{env.now:.2f}: {task} arrives")
    request_start = env.now
    yield developers.request()
    delay = env.now - request_start
    print(f"{env.now:.1f}: {task} starts after delay {delay:.2f}")
    yield env.timeout(task._duration)
    print(f"{env.now:.1f}: {task} finishes")


def generate_tasks(env, developers):
    """Generates tasks at random intervals."""

    while True:
        yield env.timeout(random.expovariate(1.0 / TASK_ARRIVAL_RATE))
        env.process(simulate_task(env, developers, TaskUniform()))


def main(args):
    """Run simulation."""

    env = simpy.Environment()
    developers = simpy.Resource(env, capacity=NUM_DEVELOPERS)
    env.process(generate_tasks(env, developers))
    env.run(until=SIMULATION_DURATION)
