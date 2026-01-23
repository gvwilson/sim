import time
import math
import csv
from itertools import count
from simpy import Environment, Store
import colored as cd
import numpy as np

rand = np.random.default_rng(seed=2026)
WHITE_ON_BLACK = f"{cd.fore_rgb(255, 255, 255)}{cd.back_rgb(0, 0, 0)}"
WHITE_ON_RED = f"{cd.fore_rgb(255, 255, 255)}{cd.back_rgb(255, 0, 0)}"


def calculateLight(colorItem: int):
    c = colorItem / 255

    if c < 0.03928:
        c /= 12.92
    else:
        c = math.pow((c + 0.055) / 1.055, 2.4)

    return c


def calculateLuminosity(r: int, g: int, b: int):
    return (
        0.2126 * calculateLight(r)
        + 0.7152 * calculateLight(g)
        + 0.0722 * calculateLight(b)
    )


def getContrastColor(r: int, g: int, b: int):
    LUMINOSITY_LIMIT = 0.579  # This is the Contrast Threshold, the higher it is, the more likely text will be white
    if calculateLuminosity(r, g, b) > LUMINOSITY_LIMIT:
        return cd.back_rgb(0, 0, 0)

    return cd.back_rgb(230, 230, 230)


class Job:
    _next_id = count(start=0)

    def __init__(self, job_duration):
        self.id = next(Job._next_id)
        self.duration = job_duration
        red = rand.uniform(0, 255)
        green = rand.uniform(0, 255)
        blue = rand.uniform(0, 255)
        self.fore = cd.fore_rgb(red, green, blue)
        self.back = getContrastColor(red, green, blue)

    def __str__(self):
        return f"job {self.fore}{self.back} {cd.Style.bold}{self.id} {cd.Style.reset}"

    def __repr__(self):
        return self.__str__()


def manager(env, queue, time_between_new_tasks, job_duration, tracing=True):
    while True:
        job = Job(job_duration)

        if tracing:
            print(f"\nQueue items before manager creates one more job: {queue.items}")
            print(
                f"At {WHITE_ON_BLACK} {env.now:>2}  {cd.Style.reset}, manager creates {job}"
            )

        yield queue.put(job)
        yield env.timeout(time_between_new_tasks)


def coder(env, queue, tracing=True):
    while True:
        wait_starts = env.now

        if tracing:
            print(f"\nQueue items before coder takes one job: {queue.items}")

        job = yield queue.get()

        get_job_at = env.now

        if tracing:
            if get_job_at - wait_starts > 0:
                print(
                    f"{WHITE_ON_RED}At {WHITE_ON_BLACK} {wait_starts:>2}  {WHITE_ON_RED}, coder waits{cd.Style.reset}"
                )
                print(
                    f"At {WHITE_ON_BLACK} {get_job_at:>2}  {cd.Style.reset}, coder gets {job}"
                )
            else:
                print(
                    f"At {WHITE_ON_BLACK} {get_job_at:>2}  {cd.Style.reset}, coder gets {job} without waiting"
                )

        yield env.timeout(job.duration)

        completed_job_at = env.now

        if tracing:
            print(
                f"At {WHITE_ON_BLACK} {completed_job_at:>2}  {cd.Style.reset}, code completes {job}"
            )


def run_simulation(time_between_new_tasks, job_duration, simulation_time, tracing=True):
    fieldnames = ["time", "queue_length"]

    with open("data.csv", "w") as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        csv_writer.writeheader()

    env = Environment()
    queue = Store(env)
    env.process(manager(env, queue, time_between_new_tasks, job_duration, tracing))
    env.process(coder(env, queue, tracing))

    until = simulation_time
    time_list = []
    queue_length_list = []

    while env.peek() < until:
        if tracing:
            print(
                f"{cd.Fore.yellow}{cd.Back.black}{cd.Style.bold}Environment time: {env.now} - Queue items: {cd.Style.reset}{queue.items}"
            )

        new_data = False
        prev_len = len(time_list)
        if env.now in time_list:
            time_list.pop()
            queue_length_list.pop()
        time_list.append(env.now)
        queue_length_list.append(len(queue.items))
        new_len = len(time_list)

        if new_len > prev_len:
            new_data = True

        if new_data:
            with open("data.csv", "a") as csv_file:
                csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                info = {"time": time_list[-1], "queue_length": queue_length_list[-1]}

                csv_writer.writerow(info)
        env.step()
        time.sleep(2)


_T_CREATE = 2
_T_JOB = 8
_T_SIM = 40

run_simulation(_T_CREATE, _T_JOB, _T_SIM, tracing=True)
