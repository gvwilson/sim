# Simple Simulations

-   FIXME

## A Hobby Project

-   Shae works on their hobby project for 50 minutes and then takes a 10-minute break
-   Import `Environment` from `simpy`
-   Define a generator to simulate work
    -   <code>env.timeout(<em>duration</em>)</code> creates an object that means "wait this long"
    -   `yield` suspends the worker and gives this object to [SimPy][simpy]
    -   SimPy advances its clock (does *not* actually "wait")

```{data-file=fixed_work_and_break.py}
T_WORK = 50
T_BREAK = 10


def worker(env):
    while True:
        print(f"start work at {env.now}")
        yield env.timeout(T_WORK)
        print(f"start break at {env.now}")
        yield env.timeout(T_BREAK)
```

-   To make this work:
    -   Create an `Environment`
    -   Call `worker` to create a generator object
        -   Does *not* execute function yet
	-   Pass in the environment so the generator can call `.timeout`
    -   Tell the environment how long to run

```{data-file=fixed_work_and_break.py}
T_MORNING = 4 * 60

if __name__ == "__main__":
    env = Environment()
    proc = worker(env)
    env.process(proc)
    env.run(until=T_MORNING)
    print(f"done at {env.now}")
```

-   Output

```{data-file=fixed_work-and_break.out}
start work at 0
start break at 50
start work at 60
start break at 110
start work at 120
start break at 170
start work at 180
start break at 230
done at 240
```

-   FIXME: diagram of execution

## Introducing Randomness

-   Shae starts at the same time but works for variable intervals
    -   So we have to decide how to model those intervals
-   [Uniform](g:random-uniform) is simplest

```{data-file=uniform_work_and_break.py}
T_MIN_WORK = 10
T_MAX_WORK = 50


def t_work():
    return random.uniform(T_MIN_WORK, T_MAX_WORK)


def worker(env):
    while True:
        print(f"start work at {env.now}")
        yield env.timeout(t_work())          # changed
        print(f"start break at {env.now}")
        yield env.timeout(T_BREAK)
```
```{data-file=uniform_work_and_break.out}
start work at 0
start break at 26.67250326533211
start work at 36.67250326533211
start break at 54.79344793494629
start work at 64.7934479349463
start break at 104.87029408376178
start work at 114.87029408376178
start break at 136.94211951464072
start work at 146.94211951464072
start break at 193.03234415437063
start work at 203.03234415437063
done at 240
```

-   The program runs, but it's not useful
    -   Can't make sense of the output

## Monitoring

-   Create our own `Env` class with `rnow` property to report time to `PREC` decimal places

```{data-file=monitor_uniform_work_and_break.py}
PREC = 3


class Env(Environment):
    @property
    def rnow(self):
        return round(self.now, PREC)
```

-   Record (start, end) work times in a list
    -   Remember to get the last one
    -   Which breaks encapsulation

```{data-file=monitor_uniform_work_and_break.py}
def worker(env, log):
    while True:
        log.append([env.rnow, None])
        yield env.timeout(t_work())
        log[-1][-1] = env.rnow
        yield env.timeout(T_BREAK)
```

-   Move main body into a function
-   Initialize random number generation for reproducibility
    -   Testing and debugging are very difficult otherwise
-   Output a structured log
    -   Use JSON

```{data-file=monitor_uniform_work_and_break.py}
SEED = 12345

def main():
    """Make simulation reproducible and create structured log."""
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else SEED
    random.seed(seed)
    env = Env()
    log = []
    proc = worker(env, log)
    env.process(proc)
    env.run(until=T_MORNING)
    log[-1][-1] = env.rnow
    json.dump(log, sys.stdout, indent=2)
```
```{data-file=monitor_uniform_work_and_break.out[
  [
    0,
    26.665
  ],
  [
    36.665,
    47.072
  ],
  …more output…
  [
    204.508,
    240
  ]
]}
```

## Visualization

-   Could put the visualization in the simulation
-   But may want to visualize the data in many different ways
