"""Use a monitoring process to record queue length."""

import argparse
from itertools import count
import json
import random
from simpy import Environment, Store
import sys

PARAMS = {
    "n_programmer": 3,
    "seed": 12345,
    "t_develop_mu": 0.5,
    "t_develop_sigma": 0.6,
    "t_job_arrival": 1.0,
    "t_monitor": 5,
    "t_sim": 10,
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
        self.queue_lengths = []

    def run(self):
        Job.clear()
        self.env.process(self.monitor())
        self.env.process(manager(self))
        for i in range(self.params["n_programmer"]):
            self.env.process(programmer(self, i))
        self.env.run(until=self.params["t_sim"])

    def monitor(self):
        while True:
            self.queue_lengths.append({"time": rv(self.env.now), "length": len(self.queue.items)})
            yield self.env.timeout(self.params["t_monitor"])

    def rand_job_arrival(self):
        return random.expovariate(1.0 / self.params["t_job_arrival"])

    def rand_develop(self):
        return random.lognormvariate(
            self.params["t_develop_mu"], self.params["t_develop_sigma"]
        )


class Job:
    SAVE = ("id", "t_create", "t_start", "t_end", "worker_id")
    _id = count()
    _all = []

    @staticmethod
    def clear():
        Job._id = count()
        Job._all = []

    def __init__(self, sim):
        Job._all.append(self)
        self.sim = sim
        self.id = next(Job._id)
        self.t_develop = sim.rand_develop()
        self.t_create = sim.env.now
        self.t_start = None
        self.t_end = None
        self.worker_id = None

    def as_json(self):
        return {key: rv(getattr(self, key)) for key in Job.SAVE}


def manager(sim):
    while True:
        yield sim.queue.put(Job(sim))
        yield sim.env.timeout(sim.rand_job_arrival())


def programmer(sim, worker_id):
    while True:
        job = yield sim.queue.get()
        job.t_start = sim.env.now
        job.worker_id = worker_id
        yield sim.env.timeout(job.t_develop)
        job.t_end = sim.env.now


def get_params():
    parser = argparse.ArgumentParser()
    parser.add_argument("--arrivals", nargs="+", help="arrival rates")
    parser.add_argument("--overrides", nargs="+", default=[], help="parameter overrides")
    args = parser.parse_args()

    arrivals = [float(a) for a in args.arrivals] if args.arrivals else [PARAMS["t_job_arrival"]]

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

    return params, arrivals


def main():
    params, arrival_rates = get_params()
    random.seed(params["seed"])
    result = []

    for rate in arrival_rates:
        p = {**params, "t_job_arrival": rate}
        sim = Simulation(p)
        sim.run()
        result.append({"params": p, "lengths": sim.queue_lengths,})

    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
