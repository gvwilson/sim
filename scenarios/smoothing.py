"""Smoothing over multiple runs with identical parameters."""

from collections import defaultdict
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from itertools import count
import json
import plotly.express as px
import random
from asimpy import Environment, Process, Queue
import sys
import util


@dataclass_json
@dataclass
class Params:
    n_iter: int = 2
    n_seed: int = 97531
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

    def simulate(self):
        Recorder.reset()
        self.queue = Queue(self)
        Manager(self)
        Coder(self)
        Monitor(self)
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
    SAVE_KEYS = ["t_create", "t_start", "t_complete"]

    def __init__(self, sim):
        super().__init__(sim)
        self.duration = self.sim.rand_job_duration()
        self.t_create = self.sim.now
        self.t_start = None
        self.t_complete = None


class Manager(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)

    async def run(self):
        while True:
            job = Job(sim=self.sim)
            await self.sim.queue.put(job)
            await self.timeout(self.sim.rand_job_arrival())


class Coder(Process):
    SAVE_KEYS = ["t_work"]

    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)
        self.t_work = 0

    def json(self):
        return {key: util.rnd(self, key) for key in self.SAVE_KEYS}

    async def run(self):
        while True:
            job = await self.sim.queue.get()
            job.t_start = self.sim.now
            await self.timeout(job.duration)
            job.t_complete = self.sim.now
            self.t_work += job.t_complete - job.t_start


class Monitor(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)

    async def run(self):
        while True:
            length = len(self.sim.queue._items)
            self.sim.lengths.append({"time": self.sim.now, "length": length})
            now = self.sim.now
            mean_age = (
                0
                if length == 0
                else sum((now - j.t_create) for j in self.sim.queue._items) / length
            )
            self.sim.ages.append({"time": self.sim.now, "mean_age": mean_age})
            await self.timeout(self.sim.params.t_monitor)


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    if args.json:
        json.dump(results, sys.stdout, indent=2)

    results = util.as_frames(results)
    ages = util.df_smooth(results["ages"], "time", "mean_age")
    fig_ages = px.line(ages, x="time", y="mean_age")
    if args.figure:
        fig_ages.write_image(args.figure[0])
    else:
        fig_ages.show()
