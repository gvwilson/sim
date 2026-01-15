from dataclasses import dataclass
from random import lognormvariate, uniform

from base import Priority, Recorder


class Job(Recorder):
    SAVE_KEYS = ["kind", "t_create", "t_start", "t_complete", "t_code", "t_test"]

    def __init__(self, sim, kind, priority, t_code=None):
        super().__init__(sim)
        self.kind = kind
        self.priority = priority
        self.t_code = self.rand_t_code() if t_code is None else t_code
        self.t_test = self.rand_t_test(self.t_code)
        self.t_create = self.sim.now
        self.t_start = None
        self.t_complete = None

    def complete(self):
        self.t_complete = self.sim.now
        return self.sim.do_nothing()

    def is_complete(self):
        return self.t_complete is not None

    def json(self):
        return {key: getattr(self, key) for key in self.SAVE_KEYS}

    def needs_decomp(self):
        return False

    def rand_t_code(self):
        return None

    def rand_t_test(self, t_code):
        return None

    def start(self):
        self.t_start = self.sim.now

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.t_create < other.t_create
        return self.priority < other.priority


class JobFragment(Job):
    def __init__(self, coder, placeholder, t_code):
        super().__init__(coder.sim, "fragment", Priority.MEDIUM, t_code=t_code)
        self.coder = coder
        self.placeholder = placeholder
        self.t_code = t_code

    def complete(self):
        super().complete()
        self.placeholder.count -= 1
        if self.placeholder.count == 0:
            self.placeholder.job.complete()
            self.placeholder.job.priority = Priority.MEDIUM
            return self.coder.queue.put(self.placeholder.job)
        else:
            return self.sim.do_nothing()


class JobIntegration(Job):
    def __init__(selef, sim):
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

    def needs_decomp(self):
        return (not self.is_complete()) and (
            self.t_code > self.sim.params.t_decomposition
        )

    def rand_t_code(self):
        return lognormvariate(self.sim.params.t_code_mean, self.sim.params.t_code_std)

    def rand_t_test(self, t_code):
        return uniform(0.5 * t_code, 1.5 * t_code)


@dataclass
class Placeholder:
    job: Job
    count: int
