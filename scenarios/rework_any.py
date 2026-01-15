"""Multiple workers re-doing work."""

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
    n_tester: int = 1
    p_rework: float = 0.5
    t_job_arrival: float = 2.0
    t_job_mean: float = 0.5
    t_job_std: float = 0.6
    t_monitor: float = 5.0
    t_sim: float = 200


class Simulation(Environment):
    def __init__(self):
        super().__init__()
        self.params = Params()
        self.code_queue = None
        self.test_queue = None
        self.lengths = []
        self.ages = []

    def simulate(self):
        Recorder.reset()
        self.code_queue = Store(self)
        self.test_queue = Store(self)

        self.process(Manager(self).run())

        for _ in range(self.params.n_coder):
            self.process(Coder(self).run())

        for _ in range(self.params.n_tester):
            self.process(Tester(self).run())

        self.process(Monitor(self).run())
        self.run(until=self.params.t_sim)

    def result(self):
        return {
            "jobs": [job.json() for job in Recorder._all[Job]],
            "lengths": self.lengths,
            "ages": self.ages,
            "coders": [coder.json() for coder in Recorder._all[Coder]],
            "testers": [tester.json() for tester in Recorder._all[Tester]],
        }

    def rand_job_arrival(self):
        return random.expovariate(1.0 / self.params.t_job_arrival)

    def rand_job_duration(self):
        return random.lognormvariate(self.params.t_job_mean, self.params.t_job_std)

    def rand_rework(self):
        return random.uniform(0, 1) < self.params.p_rework


class LogWork:
    def __init__(self, name, worker, job):
        self._name = name
        self._worker = worker
        self._job = job
        self._started = None

    def __enter__(self):
        self._started = self._worker.sim.now
        self._job.t_start.append(
            {"name": self._name, "event": "start", "time": self._started}
        )

    def __exit__(self, exc_type, exc_value, traceback):
        ended = self._worker.sim.now
        self._job.t_end.append({"name": self._name, "event": "end", "time": ended})
        self._worker.t_work += ended - self._started


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
    SAVE_KEYS = ["t_create", "t_start", "t_complete"]

    def __init__(self, sim):
        super().__init__(sim)
        self.duration = self.sim.rand_job_duration()
        self.t_create = self.sim.now
        self.t_complete = None
        self.t_start = []
        self.t_end = []


class Manager(Recorder):
    def run(self):
        while True:
            job = Job(sim=self.sim)
            yield self.sim.code_queue.put(job)
            yield self.sim.timeout(self.sim.rand_job_arrival())


class Coder(Recorder):
    SAVE_KEYS = ["t_work"]

    def __init__(self, sim):
        super().__init__(sim)
        self.t_work = 0

    def run(self):
        while True:
            job = yield self.sim.code_queue.get()
            with LogWork("code", self, job):
                yield self.sim.timeout(job.duration)
            yield self.sim.test_queue.put(job)


class Tester(Recorder):
    SAVE_KEYS = ["t_work"]

    def __init__(self, sim):
        super().__init__(sim)
        self.t_work = 0

    def run(self):
        while True:
            job = yield self.sim.test_queue.get()
            with LogWork("test", self, job):
                yield self.sim.timeout(job.duration)
            if self.sim.rand_rework():
                yield self.sim.code_queue.put(job)
            else:
                job.t_complete = self.sim.now


class Monitor(Recorder):
    def run(self):
        all_queues = (("code", self.sim.code_queue), ("test", self.sim.test_queue))
        while True:
            now = self.sim.now
            for name, queue in all_queues:
                length = len(queue.items)
                self.sim.lengths.append({"time": now, "name": name, "length": length})
                mean_age = (
                    0
                    if length == 0
                    else sum((now - j.t_create) for j in queue.items) / length
                )
                self.sim.ages.append({"time": now, "name": name, "mean_age": mean_age})
            yield self.sim.timeout(self.sim.params.t_monitor)


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    json.dump(results, sys.stdout, indent=2)
