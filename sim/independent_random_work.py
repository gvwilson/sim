"""Simulate workers running in parallel with no interaction."""

import random

import simpy

NUM_WORKERS = 3
SIMULATION_DURATION = 10
TASK_ARRIVAL_RATE = 3


def worker(env, worker_id):
    """Worker with fixed-time tasks."""
    task_id = 0
    while True:
        task_time = random.expovariate(1 / TASK_ARRIVAL_RATE)
        print(f"{env.now:.2f}: W{worker_id} starts J{task_id} = {task_time:.2f}")
        yield env.timeout(task_time)
        print(f"{env.now:.2f}: W{worker_id} finishes J{task_id}")
        task_id += 1


def main(args):
    """Run simulation."""
    env = simpy.Environment()
    for i in range(NUM_WORKERS):
        env.process(worker(env, i))
    env.run(until=SIMULATION_DURATION)
    print(f"{env.now}: complete")
