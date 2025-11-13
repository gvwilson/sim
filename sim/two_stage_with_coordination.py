"""Pools of developers and testers with handoff time."""

import random
import simpy
from util import TaskUniform, DeveloperUniform, TesterUniform


def simulate_task(params, env, developers, testers, task):
    """Simulate a task flowing through the system."""

    print(f"{env.now:.2f}: {task} arrives")
    developer = yield from simulate_development(env, developers, task)
    tester = yield from simulate_coordination(params, env, developers, testers, task, developer._id)
    yield from simulate_testing(env, testers, tester, task)


def simulate_development(env, developers, task):
    """Simulate development."""

    developer = yield developers.get()
    actual_duration = task._duration / developer._speed
    print(f"{env.now:.2f}: development {task} starts on {developer}")
    yield env.timeout(actual_duration)
    print(f"{env.now:.2f}: {task} finishes")
    yield developers.put(developer)
    return developer


def simulate_coordination(params, env, developers, testers, task, developer_id):
    """Simulate coordination of developer and a tester."""

    print(f"{env.now:.2f}: coordination for {task} starts")
    temp = yield simpy.AllOf(
        env,
        [developers.get(lambda item: item._id == developer_id),
         testers.get()]
    )
    developer = temp.events[0].value
    tester = temp.events[1].value
    print(f"{env.now:.2f}: coordination for {task} with {developer} and {tester}")
    yield env.timeout(task._duration * params["handoff_fraction"])
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


def generate_tasks(params, env, developers, testers):
    """Generates tasks at random intervals."""

    while True:
        yield env.timeout(random.expovariate(1.0 / params["task_arrival_rate"]))
        env.process(simulate_task(params, env, developers, testers, TaskUniform()))


def main(params):
    """Run simulation."""

    env = simpy.Environment()

    developers = simpy.FilterStore(env, capacity=params["num_developers"])
    developers.items = [DeveloperUniform() for _ in range(params["num_developers"])]

    testers = simpy.FilterStore(env, capacity=params["num_testers"])
    testers.items = [TesterUniform() for _ in range(params["num_testers"])]

    env.process(generate_tasks(params, env, developers, testers))
    env.run(until=params["simulation_duration"])
