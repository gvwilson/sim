"""Jobs go back to original programmer."""

import argparse
from itertools import count, product
import json
import random
from simpy import Environment, Store
import sys

PARAMS = {
    "n_programmer": (2, 3, 4),
    "n_tester": (2, 3, 4),
    "p_rework": (0.2, 0.4, 0.6, 0.8),
    "seed": 12345,
    "t_dev_mu": 1.5,
    "t_dev_sigma": 1.0,
    "t_job_arrival": 5.0,
    "t_monitor": 5,
    "t_sim": 1000,
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
        self.prog_queue = Store(self.env)
        self.test_queue = Store(self.env)
        self.lengths = []

    def run(self):
        Job.clear()
        self.env.process(self.monitor())
        self.env.process(creator(self))
        self.programmers = [Programmer(self, i) for i in range(self.params["n_programmer"])]
        self.testers = [Tester(self, i) for i in range(self.params["n_tester"])]
        self.env.run(until=self.params["t_sim"])

    def monitor(self):
        details = (("prog", self.prog_queue), ("test", self.test_queue))
        while True:
            for (name, queue) in details:
                self.lengths.append(
                    {"time": rv(self.env.now), "queue": name, "length": len(queue.items)}
                )
            yield self.env.timeout(self.params["t_monitor"])

    def rand_dev(self):
        return random.lognormvariate(
            self.params["t_dev_mu"], self.params["t_dev_sigma"]
        )

    def rand_job_arrival(self):
        return random.expovariate(1.0 / self.params["t_job_arrival"])

    def rand_rework(self):
        return random.uniform(0, 1) < self.params["p_rework"]


class Job:
    SAVE = ("id", "t_create", "done", "n_prog", "t_prog", "n_test", "t_test")
    _id = count()
    _all = []

    @staticmethod
    def clear():
        Job._id = count()
        Job._all = []

    def __init__(self, sim):
        Job._all.append(self)
        self.id = next(Job._id)
        self.t_create = sim.env.now
        self.done = False
        self.programmer_id = None
        self.n_prog = 0
        self.t_prog = 0
        self.tester_id = None
        self.n_test = 0
        self.t_test = 0

    def as_json(self):
        return {key: rv(getattr(self, key)) for key in Job.SAVE}


def creator(sim):
    while True:
        yield sim.prog_queue.put(Job(sim))
        yield sim.env.timeout(sim.rand_job_arrival())


class Worker:
    def __init__(self, sim, id):
        self.sim = sim
        self.id = id
        self.proc = sim.env.process(self.run())


class Programmer(Worker):
    def run(self):
        while True:
            job = yield self.sim.prog_queue.get()
            job.programmer_id = self.id
            start = self.sim.env.now
            yield self.sim.env.timeout(self.sim.rand_dev())
            job.n_prog += 1
            job.t_prog += self.sim.env.now - start
            yield self.sim.test_queue.put(job)


class Tester(Worker):
    def run(self):
        while True:
            job = yield self.sim.test_queue.get()
            job.tester_id = self.id
            start = self.sim.env.now
            yield self.sim.env.timeout(self.sim.rand_dev())
            job.n_test += 1
            job.t_test += self.sim.env.now - start
            if self.sim.rand_rework():
                yield self.sim.prog_queue.put(job)
            else:
                job.done = True


def main():
    random.seed(PARAMS["seed"])
    result = []
    combinations = product(PARAMS["n_programmer"], PARAMS["n_tester"], PARAMS["p_rework"])
    for (n_programmer, n_tester, p_rework) in combinations:
        sweep = {"n_programmer": n_programmer, "n_tester": n_tester, "p_rework": p_rework}
        params = {**PARAMS, **sweep}
        sim = Simulation(params)
        sim.run()
        result.append({
            "params": params,
            "lengths": sim.lengths,
            "jobs": [job.as_json() for job in Job._all],
        })
    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
