from dataclasses import dataclass
from random import lognormvariate, uniform

from recorder import Recorder
from util import Priority


class Job(Recorder):
    SAVE_KEYS = ["kind", "t_create", "t_start", "t_code", "t_code_done"]

    def __init__(self, sim, kind, priority, t_code=None):
        super().__init__(sim)
        self.kind = kind
        self.priority = priority
        self.t_code = self.rand_t_code() if t_code is None else t_code
        self.t_code_done = 0
        self.t_create = self.sim.now
        self.t_start = None

    def __str__(self):
        return f"{self.__class__.__name__}({self.t_code}>={self.t_code_done})"

    def complete(self):
        self.t_code_done = self.t_code

    def is_complete(self):
        return self.t_code_done == self.t_code

    def json(self):
        return {key: getattr(self, key) for key in self.SAVE_KEYS}

    def rand_t_code(self):
        return None

    def start(self):
        self.t_start = self.sim.now

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.t_create < other.t_create
        return self.priority < other.priority


class JobIntegration(Job):
    def __init__(self, sim):
        super().__init__(sim, "integration", Priority.LOW)

    def rand_t_code(self):
        return self.sim.params.t_integration


class JobInterrupt(Job):
    def __init__(self, sim):
        super().__init__(sim, "interrupt", Priority.HIGH)

    def rand_t_code(self):
        return lognormvariate(
            self.sim.params.t_interrupt_mean, self.sim.params.t_interrupt_std
        )


class JobRegular(Job):
    def __init__(self, sim):
        super().__init__(sim, "regular", Priority.LOW)

    def rand_t_code(self):
        return lognormvariate(self.sim.params.t_code_mean, self.sim.params.t_code_std)
