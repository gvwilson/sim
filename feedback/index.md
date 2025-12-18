# Feedback

-   Because programmers don't always get it right the first time

## Adding Testers

-   Parameter sweeping once again

```{.python data-file=simple_testing.py}
PARAMS = {
    "n_programmer": (2, 3, 4),
    "n_tester": (2, 3, 4),
    "p_rework": (0.2, 0.4, 0.6, 0.8),
    …as before…
}

def main():
    random.seed(PARAMS["seed"])
    result = []
    combinations = product(PARAMS["n_programmer"], PARAMS["n_tester"], PARAMS["p_rework"])
    for (n_programmer, n_tester, p_rework) in combinations:
        sweep = {"n_programmer": n_programmer, "n_tester": n_tester, "p_rework": p_rework}
        params = {**PARAMS, **sweep}
        sim = Simulation(params)
        sim.run()
        result.append({
            "params": params,
            "lengths": sim.lengths,
            "jobs": [job.as_json() for job in Job._all],
        })
    json.dump(result, sys.stdout, indent=2)
```

-   Two queues

```{.python data-file=simple_testing.py}
class Simulation:
    def __init__(self, params):
        self.params = params
        self.env = Environment()
        self.prog_queue = Store(self.env)
        self.test_queue = Store(self.env)
        self.lengths = []
```

-   Programmers get from one queue and add to another

```{.python data-file=simple_testing.py}
def programmer(sim, worker_id):
    while True:
        job = yield sim.prog_queue.get()
        start = sim.env.now
        yield sim.env.timeout(sim.rand_dev())
        job.n_prog += 1
        job.t_prog += sim.env.now - start
        yield sim.test_queue.put(job)
```

-   Testers get from the second queue and either recirculate the job or mark it as done

```{.python data-file=simple_testing.py}
def tester(sim, tester_id):
    while True:
        job = yield sim.test_queue.get()
        start = sim.env.now
        yield sim.env.timeout(sim.rand_dev())
        job.n_test += 1
        job.t_test += sim.env.now - start
        if sim.rand_rework():
            yield sim.prog_queue.put(job)
        else:
            job.done = True
```

-   Queue lengths

<div class="center">
  <img src="analyze_simple_testing_queues_1000.svg" alt="queue lengths">
</div>

-   Times for jobs that were started

</div>
  <img src="analyze_simple_testing_times_1000.svg" alt="Programming and testing times">
</div>

-   Gosh, this is hard to understand…

## Using Classes

-   [Simula][simula]: object-oriented programming was invented to support simulation
-   Before making our simulation more realistic, [refactor](g:refactor) to use classes
-   `Simulation` creates objects for programmers and testers
    -   Their classes are responsible for creating and running generators

```{.python data-file=class_testing.py}
class Simulation:
    …all other code as before…
    def run(self):
        Job.clear()
        self.env.process(self.monitor())
        self.env.process(creator(self))
        self.programmers = [Programmer(self, i) for i in range(self.params["n_programmer"])]
        self.testers = [Tester(self, i) for i in range(self.params["n_tester"])]
        self.env.run(until=self.params["t_sim"])
```

-   Generic `Worker` stores a reference to the simulation and its ID
-   Then calls a `.run` method and saves a reference to the generator
    -   In case we want to interrupt it

```{.python data-file=class_testing.py}
class Worker:
    def __init__(self, sim, id):
        self.sim = sim
        self.id = id
        self.proc = sim.env.process(self.run())
```

-   `Programmer` implements `.run`
    -   Identical to previous naked generator except `sim` becomes `self.sim`
-   Similar change to `Tester` (not shown here)

```{.python data-file=class_testing.py}
class Programmer(Worker):
    def run(self):
        while True:
            job = yield self.sim.prog_queue.get()
            job.programmer_id = self.id
            start = self.sim.env.now
            yield self.sim.env.timeout(self.sim.rand_dev())
            job.n_prog += 1
            job.t_prog += self.sim.env.now - start
            yield self.sim.test_queue.put(job)
```

-   We haven't changed the order of operations…
-   …so the random number generator should produce the same values at the same moments…
-   …so we can test our changes by checking that the output of the refactored version
    is identical to the output of the original version

[simula]: https://en.wikipedia.org/wiki/Simula
