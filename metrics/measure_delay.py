"""Measure time from job creation to job completion."""

from dataclasses import dataclass
from dataclasses_json import dataclass_json
from itertools import count
import json
import polars as pl
import plotly.express as px
import random
from simpy import Environment, Store
import sys
import util


@dataclass_json
@dataclass
class Params:
    n_seed: int = 13542
    t_job_interval: float = 2.0
    t_job_mean: float = 0.5
    t_job_std: float = 0.6
    t_sim: float = 10


class Simulation(Environment):
    def __init__(self):
        super().__init__()
        self.params = Params()
        self.queue = Store(self)

    def simulate(self):
        Job.reset()
        self.queue = Store(self)
        self.process(manager(self))
        self.process(coder(self))
        self.run(until=self.params.t_sim)

    def result(self):
        return {"jobs": [job.json() for job in Job._all]}

    def rand_job_arrival(self):
        return random.expovariate(1.0 / self.params.t_job_interval)

    def rand_job_duration(self):
        return random.lognormvariate(self.params.t_job_mean, self.params.t_job_std)


class Job:
    SAVE_KEYS = ["t_create", "t_start", "t_complete"]
    _next_id = count()
    _all = []

    @classmethod
    def reset(cls):
        cls._next_id = count()
        cls._all = []

    def __init__(self, sim):
        Job._all.append(self)
        self.id = next(Job._next_id)
        self.duration = sim.rand_job_duration()
        self.t_create = sim.now
        self.t_start = None
        self.t_complete = None

    def json(self):
        return {key: util.rnd(self, key) for key in self.SAVE_KEYS}


def manager(sim):
    while True:
        job = Job(sim=sim)
        yield sim.queue.put(job)
        yield sim.timeout(sim.rand_job_arrival())


def coder(sim):
    while True:
        job = yield sim.queue.get()
        job.t_start = sim.now
        yield sim.timeout(job.duration)
        job.t_complete = sim.now


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    if args.json:
        json.dump(results, sys.stdout, indent=2)
        sys.exit(0)

    results = util.as_frames(results)
    if args.tables:
        for key, frame in results.items():
            print(f"## {key}")
            print(frame)

    jobs = (
        results["jobs"]
        .filter(pl.col("t_start").is_not_null())
        .sort("t_create")
        .with_columns((pl.col("t_start") - pl.col("t_create")).alias("delay"))
    )
    fig = px.line(jobs, x="t_start", y="delay", facet_col="t_sim")
    if args.figure:
        fig.write_image(args.figure[0])
    else:
        fig.show()
