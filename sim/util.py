"""Shared code."""

import random


MAX_TASK_DURATION = 5
MAX_SPEED = 4


class TaskUniform:
    """Task with uniformly-distributed durations."""

    _id = 0
    _kind = "task"

    def __init__(self, max_duration=MAX_TASK_DURATION):
        self._id = TaskUniform._id
        TaskUniform._id += 1
        self._duration = random.uniform(1, max_duration)

    def __str__(self):
        return f"task-{self._id}/{self._duration:.2f}"


class DeveloperUniform:
    """Developer with uniformly-distributed speed."""

    _id = 0
    _kind = "developer"

    def __init__(self, max_speed=MAX_SPEED):
        self._id = DeveloperUniform._id
        DeveloperUniform._id += 1
        self._speed = random.uniform(1, max_speed)

    def __str__(self):
        return f"dev-{self._id}/{self._speed:.2f}"


class TesterUniform:
    """Tester with uniformly-distributed speed."""

    _id = 0
    _kind = "tester"

    def __init__(self, max_speed=MAX_SPEED):
        self._id = TesterUniform._id
        TesterUniform._id += 1
        self._speed = random.uniform(1, max_speed)

    def __str__(self):
        return f"test-{self._id}/{self._speed:.2f}"
