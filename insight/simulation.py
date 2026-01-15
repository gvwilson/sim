"""Base simulator with all the features."""

import json
from simpy import Environment, Store
import sys
import util

from base import Recorder
from coder import Coder
from interrupter import Interrupter
from log import Log
from jobs import JobIntegration, JobInterrupt, JobRegular
from manager import Manager
from monitor import QueueMonitor
from params import Params
from tester import Tester


class Simulation(Environment):
    def __init__(self):
        super().__init__()
        self.params = Params()
        self.code_queue = None
        self.test_queue = None
        self.log = Log(env=self)
        self.coders = []
        self.testers = []

    def do_nothing(self):
        return self.timeout(0)

    def simulate(self):
        Recorder.reset()
        self.code_queue = Store(self)
        self.test_queue = Store(self)
        Manager(self)
        Interrupter(self)
        QueueMonitor(self)
        self.coders = [Coder(self) for _ in range(self.params.n_coders)]
        self.testers = [Tester(self) for _ in range(self.params.n_testers)]
        self.run(until=self.params.t_sim)

    def result(self):
        return {
            "jobs": [
                *[job.json() for job in Recorder._all[JobIntegration]],
                *[job.json() for job in Recorder._all[JobInterrupt]],
                *[job.json() for job in Recorder._all[JobRegular]],
            ],
            "actors": self.log.actor_events,
            "queues": self.log.queue_events,
        }


if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    if args.json:
        json.dump(results, sys.stdout, indent=2)
    if args.tables:
        frames = util.as_frames(results)
        util.show_frames(frames, list(results[0]["params"].keys()))
