"""Simulate workers running in parallel with no interaction."""

import simpy

NUM_WORKERS = 3
SIMULATION_DURATION = 10


def worker(env, worker_id, task_time):
    """Worker with fixed-time tasks."""
    task_id = 0
    while True:
        print(f"{env.now:.2f}: W{worker_id} starts J{task_id}")
        yield env.timeout(task_time)
        print(f"{env.now:.2f}: W{worker_id} finishes J{task_id}")
        task_id += 1


def main(args):
    """Run simulation."""
    env = simpy.Environment()
    for i in range(NUM_WORKERS):
        env.process(worker(env, i, i + 1))
    env.run(until=SIMULATION_DURATION)
    print(f"{env.now}: complete")
