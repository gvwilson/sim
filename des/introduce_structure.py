"""Introduce structure and utilities used in examples."""

from dataclasses import dataclass
from dataclasses_json import dataclass_json
import json
from simpy import Environment
import sys
import util


@dataclass_json
@dataclass
class Params:
    """Simulation parameters."""

    n_seed: int = 13579
    t_sim: float = 30
    t_wait: float = 8


class Simulation(Environment):
    """Complete simulation."""

    def __init__(self):
        super().__init__()
        self.params = Params()
        self.log = []

    def simulate(self):
        self.process(coder(self))
        self.run(until=self.params.t_sim)

    def result(self):
        return {"log": self.log}


def coder(sim):
    """Simulate a single coder."""

    i = 0
    while True:
        sim.log.append({"time": sim.now, "message": f"loop {i}"})
        i += 1
        yield sim.timeout(sim.params.t_wait)


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    if args.json:
        json.dump(results, sys.stdout, indent=2)
    else:
        results = util.as_frames(results)
        for key, frame in results.items():
            print(f"## {key}")
            print(frame)
