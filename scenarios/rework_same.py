"""Multiple workers re-doing work with jobs going back to authors."""

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
    t_job_interval: float = 2.0
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
        self.events = []
        self.coders = []
        self.lengths = []
        self.ages = []

    def simulate(self):
        Recorder.reset()
        self.code_queue = Store(self)
        self.test_queue = Store(self)

        self.process(Manager(self).run())

        self.coders = []
        for _ in range(self.params.n_coder):
            self.coders.append(Coder(self))
            self.process(self.coders[-1].run())

        self.testers = []
        for _ in range(self.params.n_tester):
            self.process(Tester(self).run())

        self.process(Monitor(self).run())
        self.run(until=self.params.t_sim)

    def finalize(self):
        for job in Recorder._all[Job]:
            if not job.complete:
                job.update("incomplete")

    def result(self):
        self.finalize()
        return {
            "events": self.events,
            "lengths": self.lengths,
            "ages": self.ages,
            "coders": [coder.json() for coder in Recorder._all[Coder]],
            "testers": [tester.json() for tester in Recorder._all[Tester]],
        }

    def rand_job_arrival(self):
        return random.expovariate(1.0 / self.params.t_job_interval)

    def rand_job_duration(self):
        return random.lognormvariate(self.params.t_job_mean, self.params.t_job_std)

    def rand_rework(self):
        return random.uniform(0, 1) < self.params.p_rework


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
    SAVE_KEYS = ["state"]

    def __init__(self, sim):
        super().__init__(sim)
        self.duration = self.sim.rand_job_duration()
        self.t_create = sim.now
        self.complete = False
        self.coder_id = None
        self.update("waiting_code")

    def update(self, state):
        self.sim.events.append({"id": self.id, "state": state, "time": self.sim.now})
        if state == "complete":
            self.complete = True


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
        self.queue = Store(self.sim)
        self.t_work = 0

    def run(self):
        while True:
            job = yield from self.get()
            job.update("coding")
            yield self.sim.timeout(job.duration)
            job.update("test_queue")
            yield self.sim.test_queue.put(job)

    def get(self):
        new_req = self.sim.code_queue.get()
        rework_req = self.queue.get()
        result = yield (new_req | rework_req)
        if (len(result.events) == 2) or (rework_req in result):
            new_req.cancel()
            job = result[rework_req]
            assert job.coder_id == self.id
        else:
            rework_req.cancel()
            job = result[new_req]
            assert job.coder_id is None
            job.coder_id = self.id
        return job


class Tester(Recorder):
    SAVE_KEYS = ["t_work"]

    def __init__(self, sim):
        super().__init__(sim)
        self.t_work = 0

    def run(self):
        while True:
            job = yield self.sim.test_queue.get()
            assert job.coder_id is not None
            job.update("testing")
            yield self.sim.timeout(job.duration)
            if self.sim.rand_rework():
                job.update("waiting_rework")
                yield self.sim.coders[job.coder_id].queue.put(job)
            else:
                job.update("complete")
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
