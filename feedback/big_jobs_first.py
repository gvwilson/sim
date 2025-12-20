"""Jobs go back to original programmer."""

import argparse
from itertools import count, product
import json
import random
from simpy import Environment, Store
import sys

PARAMS = {
    "scenario": "any",
    "f_reduced": 0.5,
    "n_batch": 10,
    "n_programmer": 3,
    "n_tester": 3,
    "p_rework": 0.5,
    "seed": 12345,
    "t_dev_mu": 1.5,
    "t_dev_sigma": 1.0,
    "t_job_arrival": 5.0,
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

    def run(self):
        Job.clear()
        self.env.process(creator(self))
        self.programmers = [Programmer(self, i) for i in range(self.params["n_programmer"])]
        self.testers = [Tester(self, i) for i in range(self.params["n_tester"])]
        self.env.run(until=self.params["t_sim"])

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
        self.expected_prog = sim.rand_dev()
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
        delay = 0
        jobs = []
        for _ in range(sim.params["n_batch"]):
            jobs.append(Job(sim))
            delay += sim.rand_job_arrival()
        jobs.sort(key=lambda j: j.expected_prog)
        for j in jobs:
            yield sim.prog_queue.put(j)
        yield sim.env.timeout(delay)


class Worker:
    def __init__(self, sim, id):
        self.sim = sim
        self.id = id
        self.queue = Store(sim.env)
        self.proc = sim.env.process(self.run())

    def choose(self):
        if self.sim.params["scenario"] == "any":
            job = yield self.shared_queue.get()
        elif self.sim.params["scenario"] in ("same", "reduced"):
            job = yield from self.choose_same()
        else:
            assert False, f"unknown scenario {self.sim.params['scenario']}"
        return job

    def choose_same(self):
        req_shared = self.shared_queue.get()
        req_own = self.queue.get()
        result = yield (req_shared | req_own)
        if (len(result.events) == 2) or (req_own in result):
            job = result[req_own]
            req_shared.cancel()
        else:
            job = result[req_shared]
            req_own.cancel()
        return job

    def factor(self, round_trip):
        if self.sim.params["scenario"] in ("any", "same"):
            return 1.0
        elif round_trip == 0:
            return 1.0
        elif self.sim.params["scenario"] == "reduced":
            return self.sim.params["f_reduced"]
        else:
            assert False, f"unknown scenario {self.sim.params['scenario']}"


class Programmer(Worker):
    def __init__(self, sim, id):
        super().__init__(sim, id)
        self.shared_queue = self.sim.prog_queue

    def run(self):
        while True:
            job = yield from self.choose()
            job.programmer_id = self.id
            start = self.sim.env.now
            t = job.expected_prog if job.n_prog == 0 else self.sim.rand_dev()
            yield self.sim.env.timeout(self.factor(job.n_prog) * self.sim.rand_dev())
            job.n_prog += 1
            job.t_prog += self.sim.env.now - start
            if job.tester_id is None:
                yield self.sim.test_queue.put(job)
            else:
                yield self.sim.testers[job.tester_id].queue.put(job)


class Tester(Worker):
    def __init__(self, sim, id):
        super().__init__(sim, id)
        self.shared_queue = self.sim.test_queue

    def run(self):
        while True:
            job = yield from self.choose()
            job.tester_id = self.id
            start = self.sim.env.now
            yield self.sim.env.timeout(self.factor(job.n_test) * self.sim.rand_dev())
            job.n_test += 1
            job.t_test += self.sim.env.now - start
            if self.sim.rand_rework():
                yield self.sim.programmers[job.programmer_id].queue.put(job)
            else:
                job.done = True


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
        if isinstance(params[key], float):
            params[key] = float(value)
        elif isinstance(params[key], int):
            params[key] = int(value)
        elif isinstance(params[key], str):
            params[key] = value
        else:
            assert False

    return params


def main():
    params = get_params()
    random.seed(params["seed"])
    result = []
    for n_batch in (1, 5, 10, 20):
        p = {**params, "n_batch": n_batch}
        sim = Simulation(p)
        sim.run()
        result.append({
            "params": p,
            "jobs": [job.as_json() for job in Job._all],
        })
    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
