"""Shared code."""

import random


TASK_DURATION = 5


class TaskUniform:
    """Task with uniformly-distributed durations."""

    _id = 0

    def __init__(self, duration=TASK_DURATION):
        self._id = f"T{TaskUniform._id}"
        TaskUniform._id += 1
        self._duration = random.uniform(1, duration)

    def __str__(self):
        return f"{self._id}/{self._duration:.2f}"
