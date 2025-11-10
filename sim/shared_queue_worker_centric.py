"""A shared job queue with workers as processes."""

import random

import simpy


NUM_WORKERS = 3
SIMULATION_DURATION = 20
JOB_ARRIVAL_RATE = 3
JOB_DURATION = 5

def task_generator(env, queue):
    """Add tasks to the queue."""
    i = 0
    while True:
        job_time = random.expovariate(1 / JOB_ARRIVAL_RATE)
        yield env.timeout(job_time)
        job_id = f"J{i}"
        job_duration = random.expovariate(1 / JOB_DURATION)
        print(f"{env.now:.2f}: generator queueing {job_id}/{job_duration:.2f}")
        queue.put((job_id, job_duration))
        i += 1


def worker(env, queue, worker_id):
    """Take tasks from the queue and do them."""
    while True:
        print(f"{env.now:.2f}: W{worker_id} waiting")
        job_id, job_duration = yield queue.get()
        print(f"{env.now:.2f}: W{worker_id} gets {job_id}/{job_duration:.2f}")
        yield env.timeout(job_duration)
        print(f"{env.now:.2f}: W{worker_id} completes {job_id}")


def main(args):
    """Run simulation."""
    env = simpy.Environment()
    queue = simpy.Store(env)
    env.process(task_generator(env, queue))
    for i in range(NUM_WORKERS):
        env.process(worker(env, queue, i))
    env.run(until=SIMULATION_DURATION)
