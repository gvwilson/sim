"""Simulate developers running in parallel with no interaction recording themselves."""

import random
import sys
import simpy
from util import TaskRecord, DeveloperRecord, show_log


class Simulation:
    """Store assets."""

    def __init__(self, params):
        """Construct."""
        self.params = params
        self.env = simpy.Environment()

        self.devs = simpy.Store(self.env, capacity=self.params["num_developers"])
        self.devs.items = [
            DeveloperRecord(params) for _ in range(self.params["num_developers"])
        ]

    @property
    def now(self):
        """Get time."""
        return self.env.now


def generate_tasks(sim):
    """Generates tasks at random intervals."""

    while True:
        yield sim.env.timeout(random.expovariate(1.0 / sim.params["task_arrival_rate"]))
        task = TaskRecord(sim.params)
        sim.env.process(simulate_task(sim, task))


def simulate_task(sim, task):
    """Simulate a task flowing through the system."""

    task.start(sim)
    yield from simulate_development(sim, task)
    task.end(sim)


def simulate_development(sim, task):
    """Simulate development."""

    developer = yield sim.devs.get()
    task._actual = task._duration
    developer.start(sim)
    yield sim.env.timeout(task._actual)
    developer.end(sim)
    yield sim.devs.put(developer)


def main(params):
    """Run simulation."""

    sim = Simulation(params)
    sim.env.process(generate_tasks(sim))
    sim.env.run(until=sim.params["simulation_duration"])
    show_log(
        sys.stdout,
        ("task", TaskRecord._all),
        ("dev", DeveloperRecord._all),
    )
