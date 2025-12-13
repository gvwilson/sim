"""Simulate jobs with varying priorities and a weighted policy."""

import argparse
from itertools import count
import json
import random
from simpy import Environment, Store
import sys

PARAMS = {
    "n_programmer": 3,
    "n_triage": 100,
    "p_priority": (0.2, 0.8),
    "seed": 12345,
    "t_develop_mu": 0.5,
    "t_develop_sigma": 0.6,
    "t_job_arrival": 0.5,
    "t_monitor": 5,
    "t_sim": 100,
    "t_triage": 50,
}

PREC = 3


def rv(val):
    if isinstance(val, float):
        return round(val, PREC)
    return val


class WeightedStore(Store):
    def __init__(self, env):
        super().__init__(env)

    def _do_get(self, event):
        # Block if nothing available.
        if not self.items:
            return

        # Choose and return.
        item = random.choices(self.items, weights=[job.weight for job in self.items], k=1)[0]
        self.items.remove(item)
        event.succeed(item)


class Simulation:
    def __init__(self, params):
        self.params = params
        self.env = Environment()
        self.queue = WeightedStore(self.env)
        self.queue_lengths = []

    def run(self):
        Job.clear()
        self.env.process(self.monitor())
        self.env.process(Triage(self).run())
        self.env.process(manager(self))
        for i in range(self.params["n_programmer"]):
            self.env.process(programmer(self, i))
        self.env.run(until=self.params["t_sim"])

    def monitor(self):
        while True:
            lengths = dict((i, 0) for i in range(len(self.params["p_priority"])))
            for job in self.queue.items:
                lengths[job.priority] += 1
            for pri, num in lengths.items():
                self.queue_lengths.append(
                    {"time": rv(self.env.now), "priority": pri, "length": num}
                )
            yield self.env.timeout(self.params["t_monitor"])

    def rand_job_arrival(self):
        return random.expovariate(1.0 / self.params["t_job_arrival"])

    def rand_develop(self):
        return random.lognormvariate(
            self.params["t_develop_mu"], self.params["t_develop_sigma"]
        )

    def rand_priority(self):
        pri = self.params["p_priority"]
        return random.choices(list(range(len(pri))), pri, k=1)[0]


class Job:
    SAVE = ("id", "priority", "t_create", "t_start", "t_end", "t_discard", "worker_id")
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
        self.priority = sim.rand_priority()
        self.weight = len(sim.params["p_priority"]) - self.priority
        self.t_develop = sim.rand_develop()
        self.t_create = sim.env.now
        self.t_start = None
        self.t_end = None
        self.t_discard = None
        self.worker_id = None

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.t_create < other.t_create
        return self.priority < other.priority

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


class Triage:
    def __init__(self, sim):
        self.sim = sim

    def run(self):
        while True:
            yield self.sim.env.timeout(self.sim.params["t_triage"])
            p_triage = self.calculate_prob()
            if p_triage is not None:
                self.discard_items(p_triage)

    def calculate_prob(self):
        low_priority = len(self.sim.params["p_priority"]) - 1
        n_triage = self.sim.params["n_triage"]
        n_low = sum(1 if job.priority == low_priority else 0 for job in self.sim.queue.items)
        if n_low <= n_triage:
            return None
        return 1 -  (n_triage / n_low)

    def discard_items(self, p_triage):
        low_priority = len(self.sim.params["p_priority"]) - 1
        now = self.sim.env.now
        for i, job in enumerate(self.sim.queue.items):
            if job.priority != low_priority:
                continue
            if random.uniform(0, 1) < p_triage:
                self.sim.queue.items[i].t_discard = now
                del self.sim.queue.items[i]


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
    result = []

    sim = Simulation(params)
    sim.run()
    result = {
        "params": params,
        "lengths": sim.queue_lengths,
        "jobs": [job.as_json() for job in Job._all]
    }
    json.dump(result, sys.stdout, indent=2)


if __name__ == "__main__":
    main()
