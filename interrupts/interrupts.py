"""Multiple workers occasionally interrupted."""

from collections import defaultdict
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from itertools import count
import json
import random
from asimpy import Environment, Interrupt, Process, Queue
import sys
import util


@dataclass_json
@dataclass
class Params:
    n_seed: int = 97531
    n_coder: int = 2
    t_interrupt_interval: float = 5.0
    t_interrupt_mean: float = 0.2
    t_interrupt_std: float = 0.1
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
        self.coders = []
        self.lengths = []
        self.ages = []
        self.events = []

    def simulate(self):
        Recorder.reset()
        self.code_queue = Queue(self)
        Manager(self)
        self.coders = []
        for _ in range(self.params.n_coder):
            coder = Coder(self)
            self.coders.append(coder)
        Interrupter(self)
        Monitor(self)
        self.run(until=self.params.t_sim)

    def result(self):
        return {
            "jobs": [
                *[job.json() for job in Recorder._all[JobRegular]],
                *[job.json() for job in Recorder._all[JobInterrupt]],
            ],
            "events": self.events,
            "lengths": self.lengths,
            "ages": self.ages,
            "coders": [coder.json() for coder in Recorder._all[Coder]],
        }

    def rand_interrupt_arrival(self):
        return random.expovariate(1.0 / self.params.t_interrupt_interval)

    def rand_interrupt_duration(self):
        return random.lognormvariate(
            self.params.t_interrupt_mean, self.params.t_interrupt_std
        )

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
    SAVE_KEYS = [
        "id",
        "duration",
        "t_create",
        "t_start",
        "t_complete",
        "n_interrupt",
        "done",
    ]

    def __init__(self, sim, kind="regular"):
        super().__init__(sim)
        self.duration = None
        self.done = 0.0
        self.t_create = self.sim.now
        self.t_start = None
        self.t_complete = None
        self.n_interrupt = 0

    def complete(self):
        now = self.sim.now
        self.sim.events.append({"id": self.id, "event": "complete", "time": now})
        self.t_complete = now

    def interrupt(self):
        self.sim.events.append(
            {"id": self.id, "event": "interrupt", "time": self.sim.now}
        )
        self.n_interrupt += 1

    def start(self):
        now = self.sim.now
        self.sim.events.append({"id": self.id, "event": "start", "time": now})
        self.t_start = now


class JobRegular(Job):
    def __init__(self, sim):
        super().__init__(sim)
        self.duration = self.sim.rand_job_duration()


class JobInterrupt(Job):
    def __init__(self, sim):
        super().__init__(sim)
        self.duration = self.sim.rand_interrupt_duration()


class Manager(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)

    async def run(self):
        while True:
            job = JobRegular(self.sim)
            await self.sim.code_queue.put(job)
            await self.timeout(self.sim.rand_job_arrival())


class Interrupter(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)

    async def run(self):
        while True:
            await self.timeout(self.sim.rand_interrupt_arrival())
            coder = random.choice(self.sim.coders)
            coder.interrupt(JobInterrupt(self.sim))


class Coder(Process):
    SAVE_KEYS = ["n_interrupt"]

    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)
        self.t_work = 0
        self.stack = []

    def json(self):
        return {key: util.rnd(self, key) for key in self.SAVE_KEYS}

    async def run(self):
        while True:
            started = None
            try:
                # No work in hand, so get a new job.
                if len(self.stack) == 0:
                    job = await self.sim.code_queue.get()
                    job.start()
                    self.stack.append(job)
                # Current job is incomplete, so try to finish it.
                elif self.stack[-1].done < self.stack[-1].duration:
                    job = self.stack[-1]
                    started = self.sim.now
                    await self.timeout(job.duration - job.done)
                    job.done = job.duration
                # Current job is complete.
                else:
                    job = self.stack.pop()
                    job.complete()
            except Interrupt as exc:
                # Some work has been done on the current job, so save it.
                if (len(self.stack) > 0) and (started is not None):
                    now = self.sim.now
                    job = self.stack[-1]
                    job.interrupt()
                    job.done += now - started
                # Put the interrupting job on the stack.
                job = exc.cause
                job.start()
                self.stack.append(job)


class Monitor(Process):
    def init(self):
        self.sim = self._env
        cls = self.__class__
        self.id = next(Recorder._next_id[cls])
        Recorder._all[cls].append(self)

    async def run(self):
        while True:
            now = self.sim.now
            length = len(self.sim.code_queue._items)
            self.sim.lengths.append({"time": now, "length": length})
            mean_age = (
                0
                if length == 0
                else sum((now - j.t_create) for j in self.sim.code_queue._items) / length
            )
            self.sim.ages.append({"time": now, "mean_age": mean_age})
            await self.timeout(self.sim.params.t_monitor)


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    if args.json:
        json.dump(results, sys.stdout, indent=2)
    frames = util.as_frames(results)
    if args.tables:
        util.show_frames(frames, list(results[0]["params"].keys()))
