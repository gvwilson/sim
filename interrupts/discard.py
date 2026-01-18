"""Multiple workers occasionally interrupted."""

from collections import defaultdict
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from itertools import count
import json
import random
from simpy import Environment, Interrupt, Store
import sys
import util


@dataclass_json
@dataclass
class Params:
    n_seed: int = 97531
    n_coder: int = 2
    t_interrupt_interval: float = 5.0
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
        self.coders = []
        self.lengths = []
        self.ages = []

    def simulate(self):
        Recorder.reset()
        self.queue = Store(self)

        self.process(Manager(self).run())
        self.process(Interrupter(self).run())
        self.process(Monitor(self).run())

        self.coders = []
        for _ in range(self.params.n_coder):
            coder = Coder(self)
            coder.proc = self.process(coder.run())
            self.coders.append(coder)

        self.run(until=self.params.t_sim)

    def result(self):
        return {
            "jobs": [job.json() for job in Recorder._all[Job]],
            "lengths": self.lengths,
            "ages": self.ages,
            "coders": [coder.json() for coder in Recorder._all[Coder]],
        }

    def rand_interrupt_arrival(self):
        return random.expovariate(1.0 / self.params.t_interrupt_interval)

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
    SAVE_KEYS = ["id", "t_create", "t_start", "t_complete", "discarded", "duration"]

    def __init__(self, sim, kind="regular"):
        super().__init__(sim)
        self.duration = self.sim.rand_job_duration()
        self.discarded = False
        self.t_create = self.sim.now
        self.t_start = None
        self.t_complete = None


class Manager(Recorder):
    def run(self):
        while True:
            job = Job(self.sim)
            yield self.sim.queue.put(job)
            yield self.sim.timeout(self.sim.rand_job_arrival())


class Interrupter(Recorder):
    def run(self):
        while True:
            yield self.sim.timeout(self.sim.rand_interrupt_arrival())
            coder = random.choice(self.sim.coders)
            coder.proc.interrupt()


class Coder(Recorder):
    SAVE_KEYS = ["id", "n_interrupt", "t_work"]

    def __init__(self, sim):
        super().__init__(sim)
        self.n_interrupt = 0
        self.t_work = 0
        self.proc = None

    def run(self):
        while True:
            try:
                job = yield self.sim.queue.get()
                job.t_start = self.sim.now
                yield self.sim.timeout(job.duration)
                job.t_end = self.sim.now
                self.t_work += job.t_end - job.t_start
            except Interrupt:
                self.n_interrupt += 1
                job.t_end = self.sim.now
                job.discarded = True
            self.t_work += job.t_end - job.t_start


class Monitor(Recorder):
    def run(self):
        while True:
            now = self.sim.now
            length = len(self.sim.queue.items)
            self.sim.lengths.append({"time": now, "length": length})
            mean_age = (
                0
                if length == 0
                else sum((now - j.t_create) for j in self.sim.queue.items) / length
            )
            self.sim.ages.append({"time": now, "mean_age": mean_age})
            yield self.sim.timeout(self.sim.params.t_monitor)


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    if args.json:
        json.dump(results, sys.stdout, indent=2)
    frames = util.as_frames(results)
    if args.tables:
        util.show_frames(frames, list(results[0]["params"].keys()))
