"""Simulate developers running in parallel with no interaction."""

import random
import simpy


def developer(params, env, developer_id):
    """Developer with fixed-time tasks."""

    task_id = 0
    while True:
        task_time = random.expovariate(1 / params["task_arrival_rate"])
        print(f"{env.now:.2f}: W{developer_id} starts J{task_id} = {task_time:.2f}")
        yield env.timeout(task_time)
        print(f"{env.now:.2f}: W{developer_id} finishes J{task_id}")
        task_id += 1


def main(params):
    """Run simulation."""

    env = simpy.Environment()
    for i in range(params["num_developers"]):
        env.process(developer(params, env, i))
    env.run(until=params["simulation_duration"])
    print(f"{env.now}: complete")
