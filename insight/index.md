# Insights

<p id="terms"></p>

## A General-Purpose Simulator

-   Combine pieces from previous chapters and clean up a little
-   A generic `Actor` as parent for coders, managers, testers, etc.
    -   Constructor calls a lifecycle method `post_init` for extra initialization
    -   Saves the process in case we do want to interrupt it
    -   Automatically schedules the process to be run
    -   Provides a `.log` method for recording events

```{.py data-file=base.py}
class Actor(Recorder):
    def __init__(self, sim):
        super().__init__(sim)
        self.post_init()
        proc = self.run()
        self.sim.process(proc)

    def post_init(self):
        pass

    def log(self, state):
        self.sim.log.actor(self.__class__.__name__, self.id, state)
```

-   Define a `Log` class to store collected data

```{.py data-file=log.py}
@dataclass
class Log:
    env: Environment | None = None
    queue_events: list = field(default_factory=list)
    actor_events: list = field(default_factory=list)

    def queue(self, name, length):
        self.queue_events.append({"time": self.env.now, "name": name, "length": length})

    def actor(self, kind, id, state):
        self.actor_events.append({"time": self.env.now, "kind": kind, "id": id, "state": state})
```

-   Use interrupts instead of job fragmentation as discussed in [previous chapter](@/interrupts/)
-   Testers can send jobs back for rework
-   Or for integration
    -   In which case every programmer has to do some work

## The Parameterization Problem

-   There are now 15 parameters controlling the behavior of our simulation

```{.py data-file=params.py}
class Params:
    t_code_arrival: float = 2.0
    t_code_mean: float = 0.5
    t_code_std: float = 0.6
    t_decomposition: float = 0.5
    t_integration: float = 0.2
    t_interrupt_arrival: float = 5.0
    t_interrupt_mean: float = 0.2
    t_interrupt_std: float = 0.1
    t_queue_monitor: float = 5.0
    t_sim: float = 20
    n_coders: int = 2
    n_iter: int = 1
    n_seed: int = 97531
    n_testers: int = 2
    p_rework: float = 0.5
```

-   Some are completely synthetic (number of testers, queue monitoring interval, etc.)
-   But job and interrupt arrival rates, rework probability, integration times, etc. are not
-   One of the reasons to build simulations like this is to figure out
    what numbers we need to know in order to characterize our development process
-   Limited value in building a more complicated simulation if we can't get numbers for this one
