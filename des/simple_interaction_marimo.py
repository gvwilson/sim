import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    return


@app.cell
def _():
    """Simple interaction between manager and coder."""

    from itertools import count
    from simpy import Environment, Store

    T_CREATE = 6
    T_JOB = 8
    T_SIM = 20


    class Job:
        _next_id = count()

        def __init__(self):
            self.id = next(Job._next_id)
            self.duration = T_JOB

        def __str__(self):
            return f"job-{self.id}"


    def manager(env, queue):
        while True:
            job = Job()
            print(f"manager creates {job} at {env.now}")
            yield queue.put(job)
            yield env.timeout(T_CREATE)


    def coder(env, queue):
        while True:
            print(f"coder waits at {env.now}")
            job = yield queue.get()
            print(f"coder gets {job} at {env.now}")
            yield env.timeout(job.duration)
            print(f"code completes {job} at {env.now}")


    if __name__ == "__main__":
        env = Environment()
        queue = Store(env)
        env.process(manager(env, queue))
        env.process(coder(env, queue))
        env.run(until=T_SIM)
    return


if __name__ == "__main__":
    app.run()
