"""Pools of developers and testers with handoff time."""

import random
import simpy
from util import TaskUniform, DeveloperUniform, TesterUniform


NUM_DEVELOPERS = 3
NUM_TESTERS = 2
SIMULATION_DURATION = 20
TASK_ARRIVAL_RATE = 3
HANDOFF_FRACTION = 0.1
BUG_PROBABILITY = 0.6


def simulate_task(env, developers, testers, task):
    """Simulate a task flowing through the system."""

    print(f"{env.now:.2f}: {task} arrives")
    developer = None
    tester = None
    while True:
        developer = yield from simulate_development(env, developers, task, developer)
        tester = yield from simulate_coordination(env, developers, testers, task, developer, tester)
        yield from simulate_testing(env, testers, tester, task)
        if random.uniform(0, 1) < BUG_PROBABILITY:
            print(f"{env.now:.2f}: {task} is buggy")
        else:
            print(f"{env.now:.2f}: {task} is correct")
            break


def simulate_development(env, developers, task, developer=None):
    """Simulate development."""

    status = "starts" if developer is None else "resumes"
    if developer is None:
        developer = yield developers.get()
    else:
        developer = yield developers.get(lambda item: item._id == developer._id)
    actual_duration = task._duration / developer._speed
    print(f"{env.now:.2f}: development {task} {status} on {developer}")
    yield env.timeout(actual_duration)
    print(f"{env.now:.2f}: {task} finishes")
    yield developers.put(developer)
    return developer


def simulate_coordination(env, developers, testers, task, developer, tester):
    """Simulate coordination of developer and a tester."""

    print(f"{env.now:.2f}: coordination for {task} starts")
    temp = yield simpy.AllOf(
        env,
        [developers.get(lambda item: item._id == developer._id),
         testers.get(lambda item: (tester is None) or (item._id == tester._id))]
    )
    developer = temp.events[0].value
    tester = temp.events[1].value
    print(f"{env.now:.2f}: coordination for {task} with {developer} and {tester}")
    yield env.timeout(task._duration * HANDOFF_FRACTION)
    print(f"{env.now:.2f}: coordination for {task} ends")
    yield developers.put(developer)
    return tester


def simulate_testing(env, testers, tester, task):
    """Simulate testing with pre-selected tester."""

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

    developers = simpy.FilterStore(env, capacity=NUM_DEVELOPERS)
    developers.items = [DeveloperUniform() for _ in range(NUM_DEVELOPERS)]

    testers = simpy.FilterStore(env, capacity=NUM_TESTERS)
    testers.items = [TesterUniform() for _ in range(NUM_TESTERS)]

    env.process(generate_tasks(env, developers, testers))
    env.run(until=SIMULATION_DURATION)
