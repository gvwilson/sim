"""Shared code."""

from itertools import count
import csv
import random


class TaskUniform:
    """Task with uniformly-distributed durations."""

    _id = count()
    _kind = "task"

    def __init__(self, params):
        self._id = next(TaskUniform._id)
        self._duration = random.uniform(1, params["max_task_duration"])

    def __str__(self):
        return f"task-{self._id}/{self._duration:.2f}"


class DeveloperUniform:
    """Developer with uniformly-distributed speed."""

    _id = count()
    _kind = "developer"

    def __init__(self, params):
        self._id = next(DeveloperUniform._id)
        self._speed = random.uniform(1, params["max_developer_speed"])

    def __str__(self):
        return f"dev-{self._id}/{self._speed:.2f}"


class TesterUniform:
    """Tester with uniformly-distributed speed."""

    _id = count()
    _kind = "tester"

    def __init__(self, params):
        self._id = next(TesterUniform._id)
        self._speed = random.uniform(1, params["max_tester_speed"])

    def __str__(self):
        return f"test-{self._id}/{self._speed:.2f}"


class Recorder:
    """Record elapsed times."""

    def __init__(self):
        self._elapsed = 0.0
        self._current = None

    def start(self, sim):
        assert self._current is None
        self._current = sim.now

    def end(self, sim):
        assert self._current is not None
        self._elapsed += sim.now - self._current
        self._current = None


class TaskRecord(TaskUniform, Recorder):
    """Task that records time taken."""

    _all = []

    def __init__(self, params):
        super().__init__(params)
        Recorder.__init__(self)
        self._actual = None
        TaskRecord._all.append(self)


class DeveloperRecord(DeveloperUniform, Recorder):
    """Developer that records time taken."""

    _all = []

    def __init__(self, params):
        super().__init__(params)
        Recorder.__init__(self)
        DeveloperRecord._all.append(self)


class TesterRecord(TesterUniform, Recorder):
    """Tester that records time taken."""

    _all = []

    def __init__(self, params):
        super().__init__(params)
        Recorder.__init__(self)
        TesterRecord._all.append(self)


def get_log(kind, things):
    individual = [
        (kind, x._id, x._current is None, round(x._elapsed, 2))
        for x in things
    ]
    total = sum(x._elapsed for x in things)
    return individual, round(total, 2)


def show_log(stream, *args):
    log = [("kind", "id", "completed", "elapsed")]
    for (name, data) in args:
        individual, total = get_log(name, data)
        log.append((name, "total", None, total))
        log.extend(individual)
    csv.writer(stream, lineterminator="\n").writerows(log)
