"""Shared code."""

from itertools import count
import random


MAX_TASK_DURATION = 5
MAX_SPEED = 4


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
