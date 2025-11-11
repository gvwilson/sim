"""Add structured logging."""

import csv
import random
import sys
import simpy
from util import TaskUniform, DeveloperUniform, TesterUniform


NUM_DEVELOPERS = 3
NUM_TESTERS = 2
SIMULATION_DURATION = 20
TASK_ARRIVAL_RATE = 3
HANDOFF_FRACTION = 0.1
BUG_PROBABILITY = 0.6


class Simulation:
    """Store assets."""

    def __init__(self, num_developers, num_testers):
        """Construct."""
        self.env = simpy.Environment()

        self.devs = simpy.FilterStore(self.env, capacity=num_developers)
        self.devs.items = [DeveloperUniform() for _ in range(num_developers)]

        self.testers = simpy.FilterStore(self.env, capacity=num_testers)
        self.testers.items = [TesterUniform() for _ in range(num_testers)]

        self._events = [("time", "subject", "subject_id", "verb", "object", "object_id")]

    @property
    def now(self):
        """Get time."""
        return self.env.now

    def log(self, subj, verb, obj=None):
        time = round(self.now, 2)
        if obj is None:
            self._events.append((time, subj._kind, subj._id, verb, None, None))
        else:
            self._events.append((time, subj._kind, subj._id, verb, obj._kind, obj._id))

    def dump(self, stream=sys.stdout):
        csv.writer(stream, lineterminator="\n").writerows(self._events)


def simulate_task(sim, task):
    """Simulate a task flowing through the system."""

    sim.log(task, "arrives")
    developer = None
    tester = None
    while True:
        developer = yield from simulate_development(sim, task, developer)
        tester = yield from simulate_coordination(sim, task, developer, tester)
        yield from simulate_testing(sim, tester, task)
        if random.uniform(0, 1) < BUG_PROBABILITY:
            sim.log(task, "buggy")
        else:
            sim.log(task, "complete")
            break


def simulate_development(sim, task, developer=None):
    """Simulate development."""

    status = "development starts" if developer is None else "development resumes"
    if developer is None:
        developer = yield sim.devs.get()
    else:
        developer = yield sim.devs.get(lambda item: item._id == developer._id)
    actual_duration = task._duration / developer._speed
    sim.log(task, status, developer)
    yield sim.env.timeout(actual_duration)
    sim.log(task, "development finishes")
    yield sim.devs.put(developer)
    return developer


def simulate_coordination(sim, task, developer, tester):
    """Simulate coordination of developer and a tester."""

    sim.log(task, "coordination starts")
    temp = yield simpy.AllOf(
        sim.env,
        [sim.devs.get(lambda item: item._id == developer._id),
         sim.testers.get(lambda item: (tester is None) or (item._id == tester._id))]
    )
    developer = temp.events[0].value
    tester = temp.events[0].value
    sim.log(task, "coordination", developer)
    sim.log(task, "coordination", tester)
    yield sim.env.timeout(task._duration * HANDOFF_FRACTION)
    sim.log(task, "coordination ends")
    yield sim.devs.put(developer)
    return tester


def simulate_testing(sim, tester, task):
    """Simulate testing with pre-selected tester."""

    actual_duration = task._duration / tester._speed
    sim.log(task, "testing starts", tester)
    yield sim.env.timeout(actual_duration)
    sim.log(task, "testing ends")
    yield sim.testers.put(tester)


def generate_tasks(sim):
    """Generates tasks at random intervals."""

    while True:
        yield sim.env.timeout(random.expovariate(1.0 / TASK_ARRIVAL_RATE))
        sim.env.process(simulate_task(sim, TaskUniform()))


def main(args):
    """Run simulation."""

    sim = Simulation(NUM_DEVELOPERS, NUM_TESTERS)
    sim.env.process(generate_tasks(sim))
    sim.env.run(until=SIMULATION_DURATION)
    sim.dump()
