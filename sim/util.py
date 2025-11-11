"""Shared code."""

import random


MAX_TASK_DURATION = 5
MAX_WORKER_SPEED = 4


class TaskUniform:
    """Task with uniformly-distributed durations."""

    _id = 0

    def __init__(self, max_duration=MAX_TASK_DURATION):
        self._id = f"T{TaskUniform._id}"
        TaskUniform._id += 1
        self._duration = random.uniform(1, max_duration)

    def __str__(self):
        return f"{self._id}/{self._duration:.2f}"


class WorkerUniform:
    """Worker with uniformly-distributed speed."""

    _id = 0

    def __init__(self, max_speed=MAX_WORKER_SPEED):
        self._id = f"W{WorkerUniform._id}"
        WorkerUniform._id += 1
        self._speed = random.uniform(1, max_speed)

    def __str__(self):
        return f"{self._id}/{self._speed:.2f}"
