"""Manager panics occasionally, ongoing work is lost."""

import argparse
from itertools import count
import json
import random
from simpy import Environment, Interrupt, Store
import sys

PARAMS = {
    "n_programmer": 1,
    "seed": 12345,
    "t_develop_mu": 0.5,
    "t_develop_sigma": 0.6,
    "t_interrupt_arrival": 5.0,
    "t_interrupt_len": 5.0,
    "t_job_arrival": 1.0,
    "t_monitor": 5,
    "t_sim": 20,
}

PREC = 3


def rv(val):
    if isinstance(val, float):
        return round(val, PREC)
    return val


class Simulation:
    def __init__(self, params):
        self.params = params
        self.env = Environment()
        self.queue = Store(self.env)
        self.queue_length = []
        self.programmers = []

    def run(self):
        Job.clear()
        self.env.process(self.monitor())
        self.env.process(creator(self))
        self.env.process(interruptor(self))
        self.programmers = [
            self.env.process(programmer(self, i)) for i in range(self.params["n_programmer"])
        ]
        self.env.run(until=self.params["t_sim"])

    def monitor(self):
        while True:
            self.queue_length.append({"time": rv(self.env.now), "length": len(self.queue.items)})
            yield self.env.timeout(self.params["t_monitor"])

    def rand_develop(self):
        return random.lognormvariate(
            self.params["t_develop_mu"], self.params["t_develop_sigma"]
        )

    def rand_interrupt(self):
        return random.expovariate(1.0 / self.params["t_interrupt_arrival"])

    def rand_job_arrival(self):
        return random.expovariate(1.0 / self.params["t_job_arrival"])


class Job:
    SAVE = ("id", "kind", "t_create", "t_start", "t_end", "t_done", "n_interrupt", "worker_id")
    _id = count()
    _all = []

    @staticmethod
    def clear():
        Job._id = count()
        Job._all = []

    def __init__(self, sim, kind, develop):
        Job._all.append(self)
        self.kind = kind
        self.id = next(Job._id)
        self.t_develop = develop
        self.t_create = sim.env.now
        self.t_done = 0
        self.n_interrupt = 0
        self.t_start = None
        self.t_end = None
        self.worker_id = None

    def as_json(self):
        return {key: rv(getattr(self, key)) for key in Job.SAVE}


def creator(sim):
    while True:
        yield sim.queue.put(Job(sim, "regular", sim.rand_develop()))
        yield sim.env.timeout(sim.rand_job_arrival())


def interruptor(sim):
    while True:
        yield sim.env.timeout(sim.rand_interrupt())
        programmer = random.choice(sim.programmers)
        programmer.interrupt(Job(sim, "interrupt", sim.params["t_interrupt_len"]))


def programmer(sim, worker_id):
    stack = []
    while True:
        started = None
        try:
            if len(stack) == 0:
                job = yield sim.queue.get()
                job.worker_id = worker_id
                stack.append(job)
            else:
                job = stack[-1]
                if job.t_start is None:
                    job.t_start = sim.env.now
                started = sim.env.now
                yield sim.env.timeout(job.t_develop - job.t_done)
                job.t_done = job.t_develop
                job.t_end = sim.env.now
                stack.pop()
        except Interrupt as exc:
            if (len(stack) > 0) and (started is not None):
                job = stack[-1]
                job.n_interrupt += 1
                job.t_done += sim.env.now - started
            stack.append(exc.cause)


def get_params():
    parser = argparse.ArgumentParser()
    parser.add_argument("--overrides", nargs="+", default=[], help="parameter overrides")
    args = parser.parse_args()

    params = PARAMS.copy()
    for arg in args.overrides:
        fields = arg.split("=")
        assert len(fields) == 2
        key, value = fields
        assert key in params
        if isinstance(params[key], int):
            params[key] = int(value)
        elif isinstance(params[key], float):
            params[key] = float(value)
        else:
            assert False

    return params


def main():
    params = get_params()
    random.seed(params["seed"])

    sim = Simulation(params)
    sim.run()
    result = {
        "params": params,
        "lengths": sim.queue_length,
        "jobs": [job.as_json() for job in Job._all],
    }
    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
