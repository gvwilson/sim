"""Generate JSON for generic simulation."""

from collections import defaultdict
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from itertools import count
import json
import plotly.express as px
import random
from simpy import Environment, Store
import sys
import util


@dataclass_json
@dataclass
class Params:
    n_seed: int = 13542
    t_job_arrival: float = 2.0
    t_job_mean: float = 0.5
    t_job_std: float = 0.6
    t_monitor: float = 5.0
    t_sim: float = 10


class Simulation(Environment):
    def __init__(self):
        super().__init__()
        self.params = Params()
        self.queue = Store(self)
        self.lengths = []

    def simulate(self):
        Recorder.reset()
        self.queue = Store(self)
        self.process(Manager(self).run())
        self.process(Coder(self).run())
        self.process(Monitor(self).run())
        self.run(until=self.params.t_sim)

    def result(self):
        return {
            "jobs": [job.json() for job in Recorder._all[Job]],
            "lengths": self.lengths,
            "coders": [coder.json() for coder in Recorder._all[Coder]],
        }

    def rand_job_arrival(self):
        return random.expovariate(1.0 / self.params.t_job_arrival)

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


class Manager(Recorder):
    def run(self):
        while True:
            job = Job(sim=self.sim)
            yield self.sim.queue.put(job)
            yield self.sim.timeout(self.sim.rand_job_arrival())


class Coder(Recorder):
    SAVE_KEYS = ["t_work"]

    def __init__(self, sim):
        super().__init__(sim)
        self.t_work = 0

    def run(self):
        while True:
            job = yield self.sim.queue.get()
            job.t_start = self.sim.now
            yield self.sim.timeout(job.duration)
            job.t_complete = self.sim.now
            self.t_work += job.t_complete - job.t_start


class Monitor(Recorder):
    def run(self):
        while True:
            self.sim.lengths.append(
                {"time": self.sim.now, "length": len(self.sim.queue.items)}
            )
            yield self.sim.timeout(self.sim.params.t_monitor)


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    if args.json:
        json.dump(results, sys.stdout, indent=2)
    results = util.as_frames(results)
    jobs = util.df_jobs(results["jobs"])
    throughput = util.df_throughput(results["jobs"])
    utilization = util.df_utilization(results["coders"])

    fig_backlog = px.line(
        results["lengths"], x="time", y="length", color="t_job_arrival"
    )
    if args.figure:
        fig_backlog.write_image(args.figure[0])

    if args.tables:
        util.show_through_util(throughput, utilization)
