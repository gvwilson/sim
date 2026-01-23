import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Simple interaction between manager and coder
    """)
    return


@app.cell
def imports():
    # Necessary imports
    from itertools import count
    from simpy import Environment, Store
    return Environment, Store, count


@app.cell
def sim_constants():
    # Simulation constants
    T_CREATE = 6
    T_JOB = 8
    T_SIM = 20
    return T_CREATE, T_JOB, T_SIM


@app.cell
def job_class(T_JOB, count):
    class Job:
        _next_id = count()

        def __init__(self):
            self.id = next(Job._next_id)
            self.duration = T_JOB

        def __str__(self):
            return f"job-{self.id}"
    return (Job,)


@app.cell
def manager_process(Job, T_CREATE):
    def manager(env, queue):
        while True:
            job = Job()
            print(f"manager creates {job} at {env.now}")
            yield queue.put(job)
            yield env.timeout(T_CREATE)
    return (manager,)


@app.function
def coder(env, queue):
    while True:
        print(f"coder waits at {env.now}")
        job = yield queue.get()
        print(f"coder gets {job} at {env.now}")
        yield env.timeout(job.duration)
        print(f"code completes {job} at {env.now}")


@app.cell
def entry_point(Environment, Store, T_SIM, manager):
    if __name__ == "__main__":
        env = Environment()
        queue = Store(env)
        env.process(manager(env, queue))
        env.process(coder(env, queue))
        env.run(until=T_SIM)
    return


if __name__ == "__main__":
    app.run()
