"""A shared task queue with developers as processes."""

import random
import simpy
from util import TaskUniform


def generate_tasks(params, env, queue):
    """Add tasks to the queue."""

    i = 0
    while True:
        arrival_wait = random.expovariate(1 / params["task_arrival_rate"])
        yield env.timeout(arrival_wait)
        task = TaskUniform(params)
        print(f"{env.now:.2f}: generator queueing {task}")
        queue.put(task)
        i += 1


def developer(env, queue, developer_id):
    """Take tasks from the queue and do them."""

    while True:
        print(f"{env.now:.2f}: {developer_id} waiting")
        task = yield queue.get()
        print(f"{env.now:.2f}: {developer_id} gets {task}")
        yield env.timeout(task._duration)
        print(f"{env.now:.2f}: {developer_id} completes {task}")


def main(params):
    """Run simulation."""

    env = simpy.Environment()
    queue = simpy.Store(env)
    env.process(generate_tasks(params, env, queue))
    for i in range(params["num_developers"]):
        env.process(developer(env, queue, f"W{i}"))
    env.run(until=params["simulation_duration"])
