"""Calculate summary statistics from log."""

import csv
import random
import sys
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

        self._events = []

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
        header = ("time", "subject", "subject_id", "verb", "object", "object_id")
        everything = [header, *self._events]
        csv.writer(stream, lineterminator="\n").writerows(everything)


def simulate_task(sim, task):
    """Simulate a task flowing through the system."""

    sim.log(task, "arrives")
    developer = None
    tester = None
    while True:
        developer = yield from simulate_development(sim, task, developer)
        tester = yield from simulate_coordination(sim, task, developer, tester)
        yield from simulate_testing(sim, tester, task)
        if random.uniform(0, 1) < sim.params["rework_fraction"]:
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
        [
            sim.devs.get(lambda item: item._id == developer._id),
            sim.testers.get(lambda item: (tester is None) or (item._id == tester._id)),
        ],
    )
    developer = temp.events[0].value
    tester = temp.events[1].value
    sim.log(task, "coordination", developer)
    sim.log(task, "coordination", tester)
    yield sim.env.timeout(task._duration * sim.params["handoff_fraction"])
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
        yield sim.env.timeout(random.expovariate(1.0 / sim.params["task_arrival_rate"]))
        sim.env.process(simulate_task(sim, TaskUniform()))


def calculate_statistics(sim):
    """Calculate and display summary statistics."""
    durations = {}
    for time, subj, subj_id, verb, obj, obj_id in sim._events:
        if verb == "arrives":
            assert (subj == "task") and ((subj, subj_id) not in durations)
            durations[(subj, subj_id)] = (False, time)
        elif verb == "complete":
            assert (subj == "task") and ((subj, subj_id) in durations)
            durations[(subj, subj_id)] = (True, time - durations[(subj, subj_id)][1])
    for (subj, subj_id), (completed, time) in sorted(durations.items()):
        if completed:
            print(f"{subj} {subj_id}: elapsed {time:.2f}")
        else:
            print(
                f"{subj} {subj_id}: incomplete {(sim.params['simulation_duration'] - time):.2f}"
            )


def main(sim):
    """Run simulation."""

    sim = Simulation(sim)
    sim.env.process(generate_tasks(sim))
    sim.env.run(until=sim.params["simulation_duration"])

    calculate_statistics(sim)
