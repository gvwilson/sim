"""Simulate developers running in parallel with no interaction."""

import simpy


def developer(env, developer_id, task_time):
    """Developer with fixed-time tasks."""

    task_id = 0
    while True:
        print(f"{env.now:.2f}: W{developer_id} starts J{task_id}")
        yield env.timeout(task_time)
        print(f"{env.now:.2f}: W{developer_id} finishes J{task_id}")
        task_id += 1


def main(params):
    """Run simulation."""

    env = simpy.Environment()
    for i in range(params["num_developers"]):
        env.process(developer(env, i, i + 1))
    env.run(until=params["simulation_duration"])
    print(f"{env.now}: complete")
