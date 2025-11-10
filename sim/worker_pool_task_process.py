"""Pool of workers with tasks as processes."""

import random

import simpy

from util import TaskUniform


NUM_WORKERS = 3
SIMULATION_DURATION = 20
TASK_ARRIVAL_RATE = 3


def simulate_task(env, workers, task):
    """Simulate a task flowing through the system."""
    print(f"{env.now:.2f}: {task} arrives")
    with workers.request() as req:
        request_start = env.now
        yield req
        delay = env.now - request_start
        print(f"{env.now:.1f}: {task} starts after delay {delay:.2f}")
        yield env.timeout(task._duration)
        print(f"{env.now:.1f}: {task} finishes")


def generate_tasks(env, workers):
    """Generates tasks at random intervals."""
    while True:
        yield env.timeout(random.expovariate(1.0 / TASK_ARRIVAL_RATE))
        env.process(simulate_task(env, workers, TaskUniform()))


def main(args):
    """Run simulation."""
    env = simpy.Environment()
    workers = simpy.Resource(env, capacity=NUM_WORKERS)
    env.process(generate_tasks(env, workers))
    env.run(until=SIMULATION_DURATION)
