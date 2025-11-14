"""Pool of developers with tasks as processes."""

import random
import simpy
from util import TaskUniform, DeveloperUniform


def simulate_task(env, developers, task):
    """Simulate a task flowing through the system."""

    print(f"{env.now:.2f}: {task} arrives")
    request_start = env.now
    developer = yield developers.get()
    actual_duration = task._duration / developer._speed
    delay = env.now - request_start
    print(
        f"{env.now:.2f}: {task} starts on {developer} after delay {delay:.2f} duration {actual_duration:.2f}"
    )
    yield env.timeout(actual_duration)
    print(f"{env.now:.2f}: {task} finishes")
    yield developers.put(developer)


def generate_tasks(params, env, developers):
    """Generates tasks at random intervals."""

    while True:
        yield env.timeout(random.expovariate(1.0 / params["task_arrival_rate"]))
        env.process(simulate_task(env, developers, TaskUniform()))


def main(params):
    """Run simulation."""

    env = simpy.Environment()
    developers = simpy.Store(env, capacity=params["num_developers"])
    developers.items = [DeveloperUniform() for _ in range(params["num_developers"])]
    env.process(generate_tasks(params, env, developers))
    env.run(until=params["simulation_duration"])
