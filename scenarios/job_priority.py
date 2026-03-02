"""Explore effects of job priority."""

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
    n_seed: int = 97531
    policy: str = "shortest"
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
        self.queue = Queue(self, priority=True)
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

    def __lt__(self, other):
        match self.sim.params.policy:
            case "oldest":
                return self.t_create < other.t_create
            case "newest":
                return other.t_create < self.t_create
            case "shortest":
                return self.duration < other.duration
            case "longest":
                return other.duration < self.duration
            case _:
                assert False, f"unknown policy {self.sim.params.policy}"


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
    jobs = util.df_jobs(results["jobs"])
    throughput = util.df_throughput(results["jobs"], group_col="policy")
    utilization = util.df_utilization(results["coders"], group_col="policy")

    if args.tables:
        util.show_through_util(throughput, utilization)

    fig_ages = px.line(results["ages"], x="time", y="mean_age", facet_col="policy")
    fig_backlog = px.line(results["lengths"], x="time", y="length", facet_col="policy")

    if args.figure:
        fig_ages.write_image(args.figure[0])
        fig_backlog.write_image(args.figure[1])
    else:
        fig_ages.show()
        fig_backlog.show()
