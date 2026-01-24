# Discrete Event Simulation

<p id="terms"></p>

## Our First Simulation

-   Create a SimPy `Environment`
-   Create one or more [generators](g:generator) for it to run
    -   These will almost always need the environment
    -   **Environment works as event loop in Javascript ([Event discrete simulation with SimPy by Stefan Scherfke on EuroPython 2014](https://www.youtube.com/watch?v=Bk91DoAEcjY))**
-   Pass each generator to `env.process(…)`
-   Call `env.run(…)` and specify simulation duration

[![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/notebooks/nb_KA9jrHF8iGGMvgZ1DL1DF5)
```{.py data-file=ask_for_work.py}
"""
A developer ask for work at regular intervals.
A Scrum Master answers one single time informing there is available and ready work.
There is no interaction between them at this moment.
"""

from simpy import Environment

# Duration of simulation is 30 units of time
T_SIM = 30

# Time between coder asks for more available work. 8 units of time
# if unit of time is hour, it means that coder asks once per day
T_WAIT = 8


def coder(env):
    """
    A generator that emulates some behavior of a code such as asking for more available work
    """
    while True:
        print(f"{env.now}: Is there any work?")
        yield env.timeout(T_WAIT)


def scrum_master(env):
    """
    A generator that emulates some behavior of a Scrum Master such as making sure that
    there is available work for the developers
    (here concepts like Definition of Ready - DoR jumps in)
    """
    yield env.timeout(14)
    print(f"{env.now}: There is a new task available for you, developer.")


if __name__ == "__main__":
    # Create a SimPy environment
    env = Environment()

    # Create a process where coder is the generator function
    env.process(coder(env))

    # Create a process where a scrum master is the generator function
    env.process(scrum_master(env))

    # Run the simulation for the specified duration
    env.run(until=T_SIM)
```
<p style="text-align: right"><strong>See content of this file at <a href="https://github.com/gvwilson/sim/blob/main/des/ask_for_work.py">ask_for_work.py</a><strong></p>

-   Output

```{.txt data-file=ask_for_work.txt}
0: Is there any work?
8: Is there any work?
14: There is a new task available for you, developer.
16: Is there any work?
24: Is there any work?
```

## Interaction

-   Manager creates jobs and puts them in a queue
    -   **Maybe it would be good to be explicit of how jobs are organized (pooled for a sprint in Scrum process or pulled by devs in a continuous queue)**
    -   Jobs arrive at regular intervals
    -   Each job has a duration
    -   **Is there any wish to emulate a planning poker to give estimated duration of jobs?**
    -   Give each job an ID for tracking
-   Coder takes jobs from the queue in order and does them
    -   **How should we handle coder specialization / seniority to decide if a job should be assigned or not to a given coder?**
-   Queue is implemented as a SimPy `Store` with `.put()` and `.get()` methods

<div class="callout" markdown="1">

-   A process (generator) only gives control back to SimPy when it yields
-   So processes must `yield` the results of `queue.put()` and `queue.get()`
    -   Writing `job = queue.get()` rather than `job = yield queue.get()` is a common mistake

</div>

-   Parameters

```{.py data-file=simple_interaction.py}
T_CREATE = 6
T_JOB = 8
T_SIM = 20
```

-   `Job` class

```{.py data-file=simple_interaction.py}
from itertools import count

class Job:
    _next_id = count()

    def __init__(self):
        self.id = next(Job._next_id)
        self.duration = T_JOB

    def __str__(self):
        return f"job-{self.id}"
```

-   `manager` process

```{.py data-file=simple_interaction.py}
def manager(env, queue):
    while True:
        job = Job()
        print(f"manager creates {job} at {env.now}")
        yield queue.put(job)
        yield env.timeout(T_CREATE)
```

-   `coder` process

```{.py data-file=simple_interaction.py}
def coder(env, queue):
    while True:
        print(f"coder waits at {env.now}")
        job = yield queue.get()
        print(f"coder gets {job} at {env.now}")
        yield env.timeout(job.duration)
        print(f"coder completes {job} at {env.now}")
```

-   Set up and run

[![Open in molab](https://molab.marimo.io/molab-shield.svg)](https://molab.marimo.io/notebooks/nb_JRMhYdHfvtGDLSvEuQsFdR)

```{.py data-file=simple_interaction.py}
if __name__ == "__main__":
    env = Environment()
    queue = Store(env)
    env.process(manager(env, queue))
    env.process(coder(env, queue))
    env.run(until=T_SIM)
```

-   Output

```{.txt data-file=simple_interaction.txt}
manager creates job-0 at 0
coder waits at 0
coder gets job-0 at 0
manager creates job-1 at 6
coder completes job-0 at 8
coder waits at 8
coder gets job-1 at 8
manager creates job-2 at 12
coder completes job-1 at 16
coder waits at 16
coder gets job-2 at 16
manager creates job-3 at 18
```

-   Easier to see as columns

<div class="row">
  <div class="col-5" markdown="1">
```{.txt data-file=simple_interaction_manager.txt}
manager creates job-0 at 0
manager creates job-1 at 6
manager creates job-2 at 12
manager creates job-3 at 18
```
  </div>
  <div class="col-1">
  </div>
  <div class="col-5" markdown="1">
```{.txt data-file=simple_interaction_coder.txt}
coder waits at 0
coder gets job-0 at 0
coder waits at 8
coder gets job-1 at 8
coder waits at 16
coder gets job-2 at 16
```
  </div>
</div>

-   But even this is hard to read

**Alternative way of presenting**:
```
Queue items before manager creates one more job: []
At   0  , manager creates job  0

Queue items before coder takes one job: [job  0 ]
At   0  , coder gets job  0  without waiting

Queue items before manager creates one more job: []
At   6  , manager creates job  1
At   8  , coder completes job  0

Queue items before coder takes one job: [job  1 ]
At   8  , coder gets job  1  without waiting

Queue items before manager creates one more job: []
At  12  , manager creates job  2
At  16  , coder completes job  1

Queue items before coder takes one job: [job  2 ]
At  16  , coder gets job  2  without waiting

Queue items before manager creates one more job: []
At  18  , manager creates job  3
```


## Uniform Rates

-   Use ranges for creation times and job durations

```{.py data-file=uniform_interaction.py}
RNG_SEED = 98765
T_CREATE = (6, 10)
T_JOB = (8, 12)
T_SIM = 20
```

-   `Job` has a random duration

```{.py data-file=uniform_interaction.py}
class Job:
    def __init__(self):
        self.id = next(Job._next_id)
        self.duration = random.uniform(*T_JOB)
```

-   `manager` waits a random time before creating the next job
    -   Format time to two decimal places for readability

```{.py data-file=uniform_interaction.py}
def manager(env, queue):
    while True:
        job = Job()
        print(f"manager creates {job} at {env.now:.2f}")
        yield queue.put(job)
        yield env.timeout(random.uniform(*T_CREATE))
```

-   Always initialize the random number generator to ensure reproducibility
    -   Hard to debug if the program behaves differently each time we run it

```{.py data-file=uniform_interaction.py}
if __name__ == "__main__":
    random.seed(RNG_SEED)
    # …as before…
```

<div class="row">
  <div class="col-5" markdown="1">
```{.txt data-file=uniform_interaction_manager.txt}
manager creates job-0 at 0.00
manager creates job-1 at 8.36
manager creates job-2 at 14.73
```
  </div>
  <div class="col-1">
  </div>
  <div class="col-5" markdown="1">
```{.txt data-file=uniform_interaction_coder.txt}
coder waits at 0.00
coder gets job-0 at 0.00
coder waits at 8.52
coder gets job-1 at 8.52
```
  </div>
</div>

## Better Random Distributions

-   Assume probability of manager generating a new job in any instant is fixed
    -   I.e., doesn't depend on how long since the last job was generated
-   If the arrival rate (jobs per tick) is λ,
    the time until the next job is an [exponential](g:random-exponential) random variable
    with mean 1/λ

<div class="center">
  <img src="exponential.svg" alt="exponential distribution">
</div>

-   Use a [log-normal](g:random-log-normal) random variable to model job lengths
    -   All job lengths are positive
    -   Most jobs are short but there are a few outliers
    -   If parameters are μ and σ, the [median](g:median) is e<sup>μ</sup>

<div class="center">
  <img src="lognormal.svg" alt="log-normal distribution">
</div>

## Better Random Interaction

-   Parameters and randomization functions

```{.py data-file=random_interaction.py}
…other parameters as before…
T_JOB_INTERVAL = 2.0
T_JOB_MEAN = 0.5
T_JOB_STD = 0.6

def rand_job_arrival():
    return random.expovariate(1.0 / T_JOB_INTERVAL)

def rand_job_duration():
    return random.lognormvariate(T_JOB_MEAN, T_JOB_STD)
```

-   Corresponding changes to `Job` and `manager`

```{.py data-file=random_interaction.py}
class Job:
    def __init__(self):
        self.id = next(Job._next_id)
        self.duration = rand_job_duration()

def manager(env, queue):
    while True:
        job = Job()
        t_delay = rand_job_arrival()
        print(f"manager creates {job} at {env.now:.2f} waits for {t_delay:.2f}")
        yield queue.put(job)
        yield env.timeout(t_delay)
```

-   Results

<div class="row">
  <div class="col-5" markdown="1">
```{.txt data-file=random_interaction_manager.txt}
manager creates job-0 at 0.00 waits for 7.96
manager creates job-1 at 7.96 waits for 0.60
manager creates job-2 at 8.56 waits for 3.70
```
  </div>
  <div class="col-1">
  </div>
  <div class="col-5" markdown="1">
```{.txt data-file=random_interaction_coder.txt}
coder waits at 0.00
coder gets job-0 at 0.00
coder waits at 0.65
coder gets job-1 at 7.96
coder waits at 8.75
coder gets job-2 at 8.75
```
  </div>
</div>

-   But this is still hard to read and analyze

## Introduce Structure

-   Requirements
    -   Save results as JSON to simplify analysis
    -   Simulation may have several pieces, so put them in one object
    -   Support [parameter sweeping](g:parameter-sweeping)
-   Store parameters in a [dataclass](g:dataclass)
    -   Each parameter must have a default value so utilities can construct instances
        without knowing anything about specific parameters
    -   Use `@dataclass_json` decorator so that utilities can [serialize](g:serialize) as JSON

```{.py data-file=introduce_structure.py}
@dataclass_json
@dataclass
class Params:
    """Simulation parameters."""

    n_seed: int = 13579
    t_sim: float = 30
    t_wait: float = 8
```

-   Define another class to store the entire simulation
    -   Derive from SimPy `Environment`
    -   Store simulation parameters as `.params`
    -   May have other structures (e.g., a log to record output)
    -   Give it a `.result()` method that returns simulation result (e.g., the log)

```{.py data-file=introduce_structure.py}
class Simulation(Environment):
    """Complete simulation."""

    def __init__(self):
        super().__init__()
        self.params = Params()
        self.log = []

    def result(self):
        return {"log": self.log}
```

-   All of the simulation process generator functions take an instance of the simulation class as an argument
    -   `sim.whatever` for elements of the SimPy `Environment`
    -   `sim.params.whatever` for parameters

```{.py data-file=introduce_structure.py}
def coder(sim):
    """Simulate a single coder."""

    while True:
        sim.log.append(f"{sim.now}: Is there any work?")
        yield sim.timeout(sim.params.t_wait)
```

-   Define a `Simulation.simulate` method that creates processes and runs the simulation
    -   Can't call it `run` because we need that method from the parent class `Environment`

```{.py data-file=introduce_structure.py}
class Simulation
    def simulate(self):
        self.process(coder(self))
        self.run(until=self.params.t_sim)
```

-   Use `util.run(…)` to run scenarios with varying parameters and get result as JSON
    -   Look in project's `utilities` directory for implementation

```{.py data-file=introduce_structure.py}
if __name__ == "__main__":
    args, results = util.run(Params, Simulation)
    if args.json:
        json.dump(results, sys.stdout, indent=2)
    else:
        results = util.as_frames(results)
        for key, frame in results.items():
            print(f"## {key}")
            print(frame)
```

-   Sample command line invocation

```{.sh data-file=introduce_structure_json.sh}
python introduce_structure.py --json t_wait=12,20 t_sim=20,30
```

-   Output

```{.json data-file=introduce_structure_json.json}
{
  "results": [
    {
      "params": {"n_seed": 13579, "t_sim": 20, "t_wait": 12},
      "log": [
        {"time": 0, "message": "loop 0"},
        {"time": 12, "message": "loop 1"}
      ]
    },
    {
      "params": {"n_seed": 13579, "t_sim": 30, "t_wait": 12},
      "log": [
        {"time": 0, "message": "loop 0"},
        {"time": 12, "message": "loop 1"},
        {"time": 24, "message": "loop 2"}
      ]
    },
    {
      "params": {"n_seed": 13579, "t_sim": 20, "t_wait": 20},
      "log": [
        {"time": 0, "message": "loop 0"}
      ]
    },
    {
      "params": {"n_seed": 13579, "t_sim": 30, "t_wait": 20},
      "log": [
        {"time": 0, "message": "loop 0"},
        {"time": 20, "message": "loop 1"}
      ]
    }
  ]
}
```

-   Convert to [Polars][polars] dataframes)
    -   Include all parameters in each dataframe to simplify later analysis

```{.sh data-file=introduce_structure_df.sh}
python introduce_structure.py --tables t_wait=12,20 t_sim=20,30
```

```{.txt data-file=introduce_structure_df.txt}
## log
shape: (8, 5)
## log
shape: (8, 6)
┌──────┬─────────┬─────┬────────┬───────┬────────┐
│ time ┆ message ┆ id  ┆ n_seed ┆ t_sim ┆ t_wait │
│ ---  ┆ ---     ┆ --- ┆ ---    ┆ ---   ┆ ---    │
│ i64  ┆ str     ┆ i32 ┆ i32    ┆ i32   ┆ i32    │
╞══════╪═════════╪═════╪════════╪═══════╪════════╡
│ 0    ┆ loop 0  ┆ 0   ┆ 13579  ┆ 20    ┆ 12     │
│ 12   ┆ loop 1  ┆ 0   ┆ 13579  ┆ 20    ┆ 12     │
│ 0    ┆ loop 0  ┆ 1   ┆ 13579  ┆ 30    ┆ 12     │
│ 12   ┆ loop 1  ┆ 1   ┆ 13579  ┆ 30    ┆ 12     │
│ 24   ┆ loop 2  ┆ 1   ┆ 13579  ┆ 30    ┆ 12     │
│ 0    ┆ loop 0  ┆ 2   ┆ 13579  ┆ 20    ┆ 20     │
│ 0    ┆ loop 0  ┆ 3   ┆ 13579  ┆ 30    ┆ 20     │
│ 20   ┆ loop 1  ┆ 3   ┆ 13579  ┆ 30    ┆ 20     │
└──────┴─────────┴─────┴────────┴───────┴────────┘
```
