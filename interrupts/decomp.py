"""Multiple workers decomposing jobs."""

from collections import defaultdict
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from itertools import count
import json
import random
from simpy import Environment, Store, PriorityStore
import sys
import util


class Priority:
    HIGH = 0
    MEDIUM = 1
    LOW = 2


@dataclass_json
@dataclass
class Params:
    n_seed: int = 97531
    n_coder: int = 2
    t_decomposition: float = 0.5
    t_interrupt_arrival: float = 5.0
    t_interrupt_mean: float = 0.2
    t_interrupt_std: float = 0.1
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
        self.coders = []
        self.lengths = []
        self.ages = []

    def do_nothing(self):
        return self.timeout(0)

    def simulate(self):
        Recorder.reset()
        self.code_queue = Store(self)
        self.process(Manager(self).run())
        self.coders = []
        for _ in range(self.params.n_coder):
            coder = Coder(self)
            self.coders.append(coder)
            coder.proc = self.process(coder.run())
        self.process(Interrupter(self).run())
        self.process(Monitor(self).run())
        self.run(until=self.params.t_sim)

    def result(self):
        return {
            "jobs": [
                *[job.json() for job in Recorder._all[JobFragment]],
                *[job.json() for job in Recorder._all[JobInterrupt]],
                *[job.json() for job in Recorder._all[JobRegular]],
            ],
            "lengths": self.lengths,
            "ages": self.ages,
            "coders": [coder.json() for coder in Recorder._all[Coder]],
        }

    def rand_interrupt_arrival(self):
        return random.expovariate(1.0 / self.params.t_interrupt_arrival)

    def rand_interrupt_duration(self):
        return random.lognormvariate(
            self.params.t_interrupt_mean, self.params.t_interrupt_std
        )

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
    SAVE_KEYS = ["t_create", "t_start", "t_complete", "duration"]

    def __init__(self, sim, priority):
        super().__init__(sim)
        self.priority = priority
        self.t_create = self.sim.now
        self.t_start = None
        self.t_complete = None

    def start(self):
        self.t_start = self.sim.now

    def complete(self):
        self.t_complete = self.sim.now
        return self.sim.do_nothing()

    def is_complete(self):
        return self.t_complete is not None

    def needs_decomp(self):
        return False

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.t_create < other.t_create
        return self.priority < other.priority


class JobFragment(Job):
    def __init__(self, coder, placeholder, duration):
        super().__init__(coder.sim, Priority.MEDIUM)
        self.coder = coder
        self.placeholder = placeholder
        self.duration = duration

    def complete(self):
        super().complete()
        self.placeholder.count -= 1
        if self.placeholder.count == 0:
            self.placeholder.job.complete()
            self.placeholder.job.priority = Priority.MEDIUM
            return self.coder.queue.put(self.placeholder.job)
        else:
            return self.sim.do_nothing()


class JobInterrupt(Job):
    def __init__(self, sim):
        super().__init__(sim, Priority.HIGH)
        self.duration = self.sim.rand_interrupt_duration()


class JobRegular(Job):
    def __init__(self, sim):
        super().__init__(sim, Priority.LOW)
        self.duration = self.sim.rand_job_duration()

    def needs_decomp(self):
        return (not self.is_complete()) and (
            self.duration > self.sim.params.t_decomposition
        )


@dataclass
class Placeholder:
    job: Job
    count: int


class Manager(Recorder):
    def run(self):
        while True:
            job = JobRegular(self.sim)
            yield self.sim.code_queue.put(job)
            yield self.sim.timeout(self.sim.rand_job_arrival())


class Interrupter(Recorder):
    def run(self):
        while True:
            yield self.sim.timeout(self.sim.rand_interrupt_arrival())
            coder = random.choice(self.sim.coders)
            yield coder.queue.put(JobInterrupt(self.sim))


class Coder(Recorder):
    SAVE_KEYS = ["t_work"]

    def __init__(self, sim):
        super().__init__(sim)
        self.queue = PriorityStore(self.sim)
        self.t_work = 0

    def run(self):
        while True:
            job = yield from self.get()
            job.start()
            if job.needs_decomp():
                yield from self.decompose(job)
            elif not job.is_complete():
                yield self.sim.timeout(job.duration)
                yield job.complete()

    def decompose(self, job):
        size = self.sim.params.t_decomposition
        num = int(job.duration / size)
        extra = job.duration - (num * size)
        durations = [extra, *[size for _ in range(num)]]
        placeholder = Placeholder(job=job, count=len(durations))
        for d in durations:
            yield self.queue.put(JobFragment(self, placeholder, d))

    def get(self):
        new_req = self.sim.code_queue.get()
        own_req = self.queue.get()
        result = yield (new_req | own_req)
        if (len(result.events) == 2) or (own_req in result):
            new_req.cancel()
            job = result[own_req]
        else:
            own_req.cancel()
            job = result[new_req]
        return job


class Monitor(Recorder):
    def run(self):
        while True:
            now = self.sim.now
            length = len(self.sim.code_queue.items)
            self.sim.lengths.append({"time": now, "length": length})
            mean_age = (
                0
                if length == 0
                else sum((now - j.t_create) for j in self.sim.code_queue.items) / length
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
