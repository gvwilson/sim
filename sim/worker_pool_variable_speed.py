"""Pool of workers with tasks as processes."""

import random

import simpy

from util import TaskUniform, WorkerUniform


NUM_WORKERS = 3
SIMULATION_DURATION = 20
TASK_ARRIVAL_RATE = 3


def simulate_task(env, workers, task):
    """Simulate a task flowing through the system."""
    print(f"{env.now:.2f}: {task} arrives")
    request_start = env.now
    worker = yield workers.get()
    actual_duration = task._duration / worker._speed
    delay = env.now - request_start
    print(f"{env.now:.2f}: {task} starts on {worker} after delay {delay:.2f} duration {actual_duration:.2f}")
    yield env.timeout(actual_duration)
    print(f"{env.now:.2f}: {task} finishes")
    yield workers.put(worker)


def generate_tasks(env, workers):
    """Generates tasks at random intervals."""
    while True:
        yield env.timeout(random.expovariate(1.0 / TASK_ARRIVAL_RATE))
        env.process(simulate_task(env, workers, TaskUniform()))


def main(args):
    """Run simulation."""
    env = simpy.Environment()
    workers = simpy.Store(env, capacity=NUM_WORKERS)
    workers.items = [WorkerUniform() for _ in range(NUM_WORKERS)]
    env.process(generate_tasks(env, workers))
    env.run(until=SIMULATION_DURATION)
