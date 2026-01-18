"""Explore effects of job priority."""

from collections import defaultdict
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from itertools import count
import json
import random
from simpy import Environment, Store
import sys
import util


@dataclass_json
@dataclass
class Params:
    n_seed: int = 97531
    n_coder: int = 2
    t_integration: float = 0.2
    t_job_interval: float = 2.0
    t_job_mean: float = 0.5
    t_job_std: float = 0.6
    t_monitor: float = 5.0
    t_sim: float = 200


class Simulation(Environment):
    def __init__(self):
        super().__init__()
        self.params = Params()
        self.queue = None
        self.lengths = []
        self.ages = []
        self.coders = []

    def simulate(self):
        Recorder.reset()
        self.queue = Store(self)
        self.process(Manager(self).run())

        self.coders = []
        for _ in range(self.params.n_coder):
            self.coders.append(Coder(self))
            self.process(self.coders[-1].run())

        self.process(Monitor(self).run())
        self.run(until=self.params.t_sim)

    def result(self):
        return {
            "jobs": [job.json() for job in Recorder._all[Job]],
            "lengths": self.lengths,
            "ages": self.ages,
            "coders": [coder.json() for coder in Recorder._all[Coder]],
        }

    def rand_job_arrival(self):
        return random.expovariate(1.0 / self.params.t_job_interval)

    def rand_job_duration(self):
        return random.lognormvariate(self.params.t_job_mean, self.params.t_job_std)


class Recorder:
    _next_id = defaultdict(count)
    _all = defaultdict(list)

    @staticmethod
    def reset():
        Recorder._next_id = defaultdict(count)
        Recorder._all = defaultdict(list)

    def __init__(self, sim):
        cls = self.__class__
        self.id = next(self._next_id[cls])
        self._all[cls].append(self)
        self.sim = sim

    def json(self):
        return {key: util.rnd(self, key) for key in self.SAVE_KEYS}


class Job(Recorder):
    SAVE_KEYS = ["kind", "t_create", "t_start", "t_complete"]

    def __init__(self, sim, kind="regular", duration=None):
        super().__init__(sim)
        self.kind = kind
        self.duration = (
            duration if duration is not None else self.sim.rand_job_duration()
        )
        self.t_create = self.sim.now
        self.t_start = None
        self.t_complete = None


class Manager(Recorder):
    def run(self):
        while True:
            job = Job(self.sim)
            yield self.sim.queue.put(job)
            yield self.sim.timeout(self.sim.rand_job_arrival())


class Coder(Recorder):
    SAVE_KEYS = ["t_work"]

    def __init__(self, sim):
        super().__init__(sim)
        self.t_work = 0
        self.queue = Store(self.sim)

    def run(self):
        while True:
            job = yield from self.get()
            job.t_start = self.sim.now
            yield self.sim.timeout(job.duration)
            job.t_complete = self.sim.now
            self.t_work += job.t_complete - job.t_start
            if job.kind == "regular":
                for coder in self.sim.coders:
                    yield coder.queue.put(
                        Job(self.sim, "integration", self.sim.params.t_integration)
                    )

    def get(self):
        new_req = self.sim.queue.get()
        integrate_req = self.queue.get()
        result = yield (new_req | integrate_req)
        if (len(result.events) == 2) or (integrate_req in result):
            new_req.cancel()
            job = result[integrate_req]
        else:
            integrate_req.cancel()
            job = result[new_req]
        return job


class Monitor(Recorder):
    def run(self):
        while True:
            length = len(self.sim.queue.items)
            self.sim.lengths.append({"time": self.sim.now, "length": length})
            now = self.sim.now
            mean_age = (
                0
                if length == 0
                else sum((now - j.t_create) for j in self.sim.queue.items) / length
            )
            self.sim.ages.append({"time": self.sim.now, "mean_age": mean_age})
            yield self.sim.timeout(self.sim.params.t_monitor)


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    json.dump(results, sys.stdout, indent=2)
