"""Multiple workers re-doing work with jobs going back to authors."""

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
        self.code_queue = Queue(self)
        self.test_queue = Queue(self)

        Manager(self)

        self.coders = []
        for _ in range(self.params.n_coder):
            self.coders.append(Coder(self))

        for _ in range(self.params.n_tester):
            Tester(self)

        Monitor(self)
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


class Manager(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)

    async def run(self):
        while True:
            job = Job(sim=self.sim)
            await self.sim.code_queue.put(job)
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
        self.rework_queue = Queue(self.sim)
        self.t_work = 0
        self._work_event = None

    def json(self):
        return {key: util.rnd(self, key) for key in self.SAVE_KEYS}

    def notify_work(self):
        """Signal that work may be available."""
        if self._work_event is not None and not self._work_event._triggered:
            self._work_event.succeed()

    async def get(self):
        """Get next job, preferring rework queue over shared queue."""
        while True:
            if not self.rework_queue.is_empty():
                job = await self.rework_queue.get()
                assert job.coder_id == self.id
                return job
            if not self.sim.code_queue.is_empty():
                job = await self.sim.code_queue.get()
                assert job.coder_id is None
                job.coder_id = self.id
                return job
            self._work_event = Event(self.sim)
            await self._work_event

    async def run(self):
        while True:
            job = await self.get()
            job.update("coding")
            await self.timeout(job.duration)
            job.update("test_queue")
            await self.sim.test_queue.put(job)


class Tester(Process):
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
            job = await self.sim.test_queue.get()
            assert job.coder_id is not None
            job.update("testing")
            await self.timeout(job.duration)
            if self.sim.rand_rework():
                job.update("waiting_rework")
                coder = self.sim.coders[job.coder_id]
                await coder.rework_queue.put(job)
                coder.notify_work()
            else:
                job.update("complete")
                job.t_complete = self.sim.now


class Monitor(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)

    async def run(self):
        all_queues = (("code", self.sim.code_queue), ("test", self.sim.test_queue))
        while True:
            now = self.sim.now
            for name, queue in all_queues:
                length = len(queue._items)
                self.sim.lengths.append({"time": now, "name": name, "length": length})
                mean_age = (
                    0
                    if length == 0
                    else sum((now - j.t_create) for j in queue._items) / length
                )
                self.sim.ages.append({"time": now, "name": name, "mean_age": mean_age})
            await self.timeout(self.sim.params.t_monitor)


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    json.dump(results, sys.stdout, indent=2)
