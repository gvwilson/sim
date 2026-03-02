"""Explore effects of job priority."""

from collections import defaultdict
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from itertools import count
import json
import random
from asimpy import Environment, Event, Process, Queue
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
        self.queue = Queue(self)
        Manager(self)

        self.coders = []
        for _ in range(self.params.n_coder):
            self.coders.append(Coder(self))

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


class Manager(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)

    async def run(self):
        while True:
            job = Job(self.sim)
            await self.sim.queue.put(job)
            for coder in self.sim.coders:
                coder.notify_work()
            await self.timeout(self.sim.rand_job_arrival())


class Coder(Process):
    SAVE_KEYS = ["t_work"]

    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)
        self.t_work = 0
        self.own_queue = Queue(self.sim)
        self._work_event = None

    def json(self):
        return {key: util.rnd(self, key) for key in self.SAVE_KEYS}

    def notify_work(self):
        """Signal that work may be available."""
        if self._work_event is not None and not self._work_event._triggered:
            self._work_event.succeed()

    async def get(self):
        """Get next job, preferring own integration queue over shared queue."""
        while True:
            if not self.own_queue.is_empty():
                return await self.own_queue.get()
            if not self.sim.queue.is_empty():
                return await self.sim.queue.get()
            self._work_event = Event(self.sim)
            await self._work_event

    async def run(self):
        while True:
            job = await self.get()
            job.t_start = self.sim.now
            await self.timeout(job.duration)
            job.t_complete = self.sim.now
            self.t_work += job.t_complete - job.t_start
            if job.kind == "regular":
                for coder in self.sim.coders:
                    await coder.own_queue.put(
                        Job(self.sim, "integration", self.sim.params.t_integration)
                    )
                    coder.notify_work()


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
    json.dump(results, sys.stdout, indent=2)
