"""Pools of developers and testers with handoff."""

import random
import simpy
from util import TaskUniform, DeveloperUniform, TesterUniform


NUM_DEVELOPERS = 3
NUM_TESTERS = 2
SIMULATION_DURATION = 20
TASK_ARRIVAL_RATE = 3


def simulate_task(env, developers, testers, task):
    """Simulate a task flowing through the system."""

    print(f"{env.now:.2f}: {task} arrives")
    yield from simulate_development(env, developers, task)
    yield from simulate_testing(env, testers, task)


def simulate_development(env, developers, task):
    """Simulate development."""

    developer = yield developers.get()
    actual_duration = task._duration / developer._speed
    print(f"{env.now:.2f}: development {task} starts on {developer}")
    yield env.timeout(actual_duration)
    print(f"{env.now:.2f}: {task} finishes")
    yield developers.put(developer)


def simulate_testing(env, testers, task):
    """Simulate testing."""

    tester = yield testers.get()
    actual_duration = task._duration / tester._speed
    print(f"{env.now:.2f}: testing {task} starts on {tester}")
    yield env.timeout(actual_duration)
    print(f"{env.now:.2f}: {task} finishes")
    yield testers.put(tester)


def generate_tasks(env, developers, testers):
    """Generates tasks at random intervals."""

    while True:
        yield env.timeout(random.expovariate(1.0 / TASK_ARRIVAL_RATE))
        env.process(simulate_task(env, developers, testers, TaskUniform()))


def main(args):
    """Run simulation."""

    env = simpy.Environment()

    developers = simpy.Store(env, capacity=NUM_DEVELOPERS)
    developers.items = [DeveloperUniform() for _ in range(NUM_DEVELOPERS)]

    testers = simpy.Store(env, capacity=NUM_TESTERS)
    testers.items = [TesterUniform() for _ in range(NUM_TESTERS)]

    env.process(generate_tasks(env, developers, testers))
    env.run(until=SIMULATION_DURATION)
