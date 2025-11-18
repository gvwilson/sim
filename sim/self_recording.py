"""Calculate summary statistics from self-recording objects."""

import random
import sys
import simpy
from util import TaskRecord, DeveloperRecord, TesterRecord, show_log


class Simulation:
    """Store assets."""

    def __init__(self, params):
        """Construct."""
        self.params = params
        self.env = simpy.Environment()

        self.devs = simpy.FilterStore(self.env, capacity=self.params["num_developers"])
        self.devs.items = [
            DeveloperRecord(params) for _ in range(self.params["num_developers"])
        ]

        self.testers = simpy.FilterStore(self.env, capacity=self.params["num_testers"])
        self.testers.items = [
            TesterRecord(params) for _ in range(self.params["num_testers"])
        ]

    @property
    def now(self):
        """Get time."""
        return self.env.now


def simulate_task(sim, task):
    """Simulate a task flowing through the system."""

    task.start(sim)
    developer = None
    tester = None
    while True:
        developer = yield from simulate_development(sim, task, developer)
        tester = yield from simulate_coordination(sim, task, developer, tester)
        yield from simulate_testing(sim, tester, task)
        if random.uniform(0, 1) >= sim.params["rework_fraction"]:
            break
    task.end(sim)


def simulate_development(sim, task, developer=None):
    """Simulate development."""

    if developer is None:
        developer = yield sim.devs.get()
    else:
        developer = yield sim.devs.get(lambda item: item._id == developer._id)
    task._actual = task._duration / developer._speed
    developer.start(sim)
    yield sim.env.timeout(task._actual)
    developer.end(sim)
    yield sim.devs.put(developer)
    return developer


def simulate_coordination(sim, task, developer, tester):
    """Simulate coordination of developer and a tester."""

    temp = yield simpy.AllOf(
        sim.env,
        [
            sim.devs.get(lambda item: item._id == developer._id),
            sim.testers.get(lambda item: (tester is None) or (item._id == tester._id)),
        ],
    )
    developer = temp.events[0].value
    tester = temp.events[1].value
    developer.start(sim)
    tester.start(sim)
    yield sim.env.timeout(task._duration * sim.params["handoff_fraction"])
    tester.end(sim)
    developer.end(sim)
    yield sim.devs.put(developer)
    return tester


def simulate_testing(sim, tester, task):
    """Simulate testing with pre-selected tester."""

    actual_duration = task._duration / tester._speed
    tester.start(sim)
    yield sim.env.timeout(actual_duration)
    tester.end(sim)
    yield sim.testers.put(tester)


def generate_tasks(sim):
    """Generates tasks at random intervals."""

    while True:
        yield sim.env.timeout(random.expovariate(1.0 / sim.params["task_arrival_rate"]))
        task = TaskRecord(sim.params)
        sim.env.process(simulate_task(sim, task))


def main(params):
    """Run simulation."""

    sim = Simulation(params)
    sim.env.process(generate_tasks(sim))
    sim.env.run(until=sim.params["simulation_duration"])
    show_log(
        sys.stdout,
        ("task", TaskRecord._all),
        ("dev", DeveloperRecord._all),
        ("tester", TesterRecord._all),
    )
