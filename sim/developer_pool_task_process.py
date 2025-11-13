"""Pool of developers with tasks as processes."""

import random
import simpy
from util import TaskUniform


def simulate_task(env, developers, task):
    """Simulate a task flowing through the system."""

    print(f"{env.now:.2f}: {task} arrives")
    request_start = env.now
    yield developers.request()
    delay = env.now - request_start
    print(f"{env.now:.1f}: {task} starts after delay {delay:.2f}")
    yield env.timeout(task._duration)
    print(f"{env.now:.1f}: {task} finishes")


def generate_tasks(params, env, developers):
    """Generates tasks at random intervals."""

    while True:
        yield env.timeout(random.expovariate(1.0 / params["task_arrival_rate"]))
        env.process(simulate_task(env, developers, TaskUniform()))


def main(params):
    """Run simulation."""

    env = simpy.Environment()
    developers = simpy.Resource(env, capacity=params["num_developers"])
    env.process(generate_tasks(params, env, developers))
    env.run(until=params["simulation_duration"])
