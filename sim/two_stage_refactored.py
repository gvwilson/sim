"""Refactor to store assets in a class."""

import random
import simpy
from util import TaskUniform, DeveloperUniform, TesterUniform


class Simulation:
    """Store assets."""

    def __init__(self, params):
        """Construct."""
        self.params = params
        self.env = simpy.Environment()

        self.devs = simpy.FilterStore(self.env, capacity=self.params["num_developers"])
        self.devs.items = [
            DeveloperUniform() for _ in range(self.params["num_developers"])
        ]

        self.testers = simpy.FilterStore(self.env, capacity=self.params["num_testers"])
        self.testers.items = [
            TesterUniform() for _ in range(self.params["num_testers"])
        ]

    @property
    def now(self):
        """Get time."""
        return self.env.now


def simulate_task(sim, task):
    """Simulate a task flowing through the system."""

    print(f"{sim.now:.2f}: {task} arrives")
    developer = None
    tester = None
    while True:
        developer = yield from simulate_development(sim, task, developer)
        tester = yield from simulate_coordination(sim, task, developer, tester)
        yield from simulate_testing(sim, tester, task)
        if random.uniform(0, 1) < sim.params["rework_fraction"]:
            print(f"{sim.now:.2f}: {task} is buggy")
        else:
            print(f"{sim.now:.2f}: {task} is correct")
            break


def simulate_development(sim, task, developer=None):
    """Simulate development."""

    status = "starts" if developer is None else "resumes"
    if developer is None:
        developer = yield sim.devs.get()
    else:
        developer = yield sim.devs.get(lambda item: item._id == developer._id)
    actual_duration = task._duration / developer._speed
    print(f"{sim.now:.2f}: development {task} {status} on {developer}")
    yield sim.env.timeout(actual_duration)
    print(f"{sim.now:.2f}: {task} finishes")
    yield sim.devs.put(developer)
    return developer


def simulate_coordination(sim, task, developer, tester):
    """Simulate coordination of developer and a tester."""

    print(f"{sim.now:.2f}: coordination for {task} starts")
    temp = yield simpy.AllOf(
        sim.env,
        [
            sim.devs.get(lambda item: item._id == developer._id),
            sim.testers.get(lambda item: (tester is None) or (item._id == tester._id)),
        ],
    )
    developer = temp.events[0].value
    tester = temp.events[1].value
    print(f"{sim.now:.2f}: coordination for {task} with {developer} and {tester}")
    yield sim.env.timeout(task._duration * sim.params["handoff_fraction"])
    print(f"{sim.now:.2f}: coordination for {task} ends")
    yield sim.devs.put(developer)
    return tester


def simulate_testing(sim, tester, task):
    """Simulate testing with pre-selected tester."""

    actual_duration = task._duration / tester._speed
    print(f"{sim.now:.2f}: testing {task} starts on {tester}")
    yield sim.env.timeout(actual_duration)
    print(f"{sim.now:.2f}: {task} finishes")
    yield sim.testers.put(tester)


def generate_tasks(sim):
    """Generates tasks at random intervals."""

    while True:
        yield sim.env.timeout(random.expovariate(1.0 / sim.params["task_arrival_rate"]))
        sim.env.process(simulate_task(sim, TaskUniform()))


def main(params):
    """Run simulation."""

    sim = Simulation(params)
    sim.env.process(generate_tasks(sim))
    sim.env.run(until=sim.params["simulation_duration"])
