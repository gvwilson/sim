# Handling Interrupts

<p id="terms"></p>

## Throwing Work Away

-   Jobs don't have priorities
-   The manager interrupts
-   Any work done on the current job is lost
    -   We'll fix this later
-   Parameters and simulation class

```{.py .python data-file=discard.py}
class Params:
    # …as before…
    t_interrupt_interval: float = 5.0

class Simulation(Environment):
    # …as before…
    def rand_interrupt_arrival(self):
        return random.expovariate(1.0 / self.params.t_interrupt_interval)
```

-   But we need a way to get at the coder's process (i.e., the generator) in order to interrupt it
    -   The `Coder` instance is something we've built around the generator
    -   `Environment.process(…)` returns the generator, so we can store that

```{.py .python data-file=discard.py}
class Simulation(Environment):
    def simulate(self):
        # …queue, manager, and monitor as before…

        self.process(Interrupter(self).run())

        self.coders = []
        for _ in range(self.params.n_coder):
            coder = Coder(self)
            coder.proc = self.process(coder.run())
            self.coders.append(coder)

        self.run(until=self.params.t_sim)
```

-   Our new `Interrupter` reaches inside a coder to get its process

```{.py data-file=discard.py}
class Interrupter(Recorder):
    def run(self):
        while True:
            yield self.sim.timeout(self.sim.rand_interrupt_arrival())
            coder = random.choice(self.sim.coders)
            coder.proc.interrupt()
```

<div class="callout" markdown="1">

-   When we call `proc.interrupt()`, SimPy raises an `Interrupt` exception inside the generator
-   But it can only do this while the framework is running, *not* while the process is running
    -   Because only one thing runs at a time
-   So the exception is only raised when the process interacts with the environment
    -   I.e., at `queue.get()`, `timeout()`, or other `yield` points

</div>

-   Write a `Coder` that throws away whatever job it's doing when it is interrupted
    -   Not realistic, but it gives us a chance to learn about interrupts

```{.py data-file=discard.py}
from simpy import Interrupt

class Coder(Recorder):
    def run(self):
        while True:
            try:
                job = yield self.sim.queue.get()
                job.t_start = self.sim.now
                yield self.sim.timeout(job.duration)
                job.t_end = self.sim.now
                self.t_work += job.t_end - job.t_start
            except Interrupt:
                self.n_interrupt += 1
                job.t_end = self.sim.now
                job.discarded = True
            self.t_work += job.t_end - job.t_start
```

-   Exercise: how does the percentage of discarded jobs change as the interrupt rate changes?

## Resuming Work

-   General idea: coders have a stack of work
    -   At most one regular job
    -   And zero or more interrupts stacked on top of it
    -   When an interrupt arrives, it goes on the top of the stack
-   Do the simple bits first
    -   Subclass `Job` so that we can call different methods for defining duration
-   Notice that we're piling up a bunch of parameters whose values we probably don't know

```{.py data-file=interrupts.py}
class Params:
    # …as before…
    t_interrupt_interval: float = 5.0
    t_interrupt_mean: float = 0.2
    t_interrupt_std: float = 0.1

class JobRegular(Job):
    def __init__(self, sim):
        super().__init__(sim)
        self.duration = self.sim.rand_job_duration()


class JobInterrupt(Job):
    def __init__(self, sim):
        super().__init__(sim)
        self.duration = self.sim.rand_interrupt_duration()
```

-   `Manager` creates `JobRegular`, `Interrupter` creates `JobInterrupt`
-   Note that `Interrupter` passes the new job to `.interrupt()` so that it becomes the exception's `.cause`

```{.py data-file=interrupts.py}
class Interrupter(Recorder):
    def run(self):
        while True:
            yield self.sim.timeout(self.sim.rand_interrupt_arrival())
            coder = random.choice(self.sim.coders)
            coder.proc.interrupt(JobInterrupt(self.sim))
```

-   It took several tries to get the `Coder` right
-   The problem is that interrupts can occur whenever the coder interacts with SimPy
    -   So if the coder does anything with SimPy in the `except` block,
        we can have an interrupt while we're handling an interrupt
-   Solution is to implement a [state machine](g:state-machine)
    1.  No work, so get a new job from the coding queue.
    2.  Job on top of the stack is incomplete, so do some work.
    3.  Job on top of the stack is complete, so pop it.
-   If an interrupt occurs:
    -   Add some time to the current job *if we actually started it*
    -   Push the new job on the stack
    -   Note: the new job arrives as the `Interrupt` exception's cause

```{.py data-file=interrupts.py}
class Coder(Recorder):
    def __init__(self, sim):
        super().__init__(sim)
        self.proc = None
        self.stack = []

    def run(self):
        while True:
            started = None
            try:
                # No work in hand, so get a new job.
                if len(self.stack) == 0:
                    job = yield self.sim.code_queue.get()
                    job.start()
                    self.stack.append(job)
                # Current job is incomplete, so try to finish it.
                elif self.stack[-1].done < self.stack[-1].duration:
                    job = self.stack[-1]
                    started = self.sim.now
                    yield self.sim.timeout(job.duration - job.done)
                    job.done = job.duration
                # Current job is complete.
                else:
                    job = self.stack.pop()
                    job.complete()
            except Interrupt as exc:
                # Some work has been done on the current job, so save it.
                if (len(self.stack) > 0) and (started is not None):
                    now = self.sim.now
                    job = self.stack[-1]
                    job.interrupt()
                    job.done += now - started
                # Put the interrupting job on the stack.
                job = exc.cause
                job.start()
                self.stack.append(job)
```

-   This works, but the code is hard to understand, debug, and extend

## Decomposing Jobs

-   Design has two parts:
    -   Treat interrupts as high-priority jobs
    -   Break regular jobs into short fragments so that interrupts are handled promptly (but not immediately)
-   Define three priorities:
    -   High: interrupt
    -   Medium: fragments of regular job
    -   Low: regular jobs

```{.py data-file=decompose.py}
class Priority:
    HIGH = 0
    MEDIUM = 1
    LOW = 2
```

-   Generic `Job` has a few [lifecycle methods](g:lifecycle-method) for child classes to override
    -   `Job.start` is called when work starts on a job
    -   `Job.complete` is called when the job is completed
    -   `Job.is_complete` tells us whether the job has been completed or not
    -   `Job.needs_decomp` tells us whether the job needs to be decomposed
-   We will explain `sim.do_nothing()` shortly

```{.py data-file=decompose.py}
class Job(Recorder):
    def __init__(self, sim, priority):
        super().__init__(sim)
        self.priority = priority
        self.t_create = self.sim.now
        self.t_start = None
        self.t_complete = None

    def start(self):
        self.t_start = self.sim.now

    def complete(self):
        self.t_complete = self.sim.now
        return self.sim.do_nothing()

    def is_complete(self):
        return self.t_complete is not None

    def needs_decomp(self):
        return False

    def __lt__(self, other):
        if self.priority == other.priority:
            return self.t_create < other.t_create
        return self.priority < other.priority
```

-   `JobInterrupt` is the simplest child class

```{.py data-file=decompose.py}
class JobInterrupt(Job):
    def __init__(self, sim):
        super().__init__(sim, Priority.HIGH)
        self.duration = self.sim.rand_interrupt_duration()
```

-   `JobRegular` overrides `.needs_decomp()`
    -   If this job isn't complete *and* the time required is greater than the decomposition threshold
    -   The latter parameter is another completely arbitrary number

```{.py data-file=decompose.py}
class JobRegular(Job):
    def __init__(self, sim):
        super().__init__(sim, Priority.LOW)
        self.duration = self.sim.rand_job_duration()

    def needs_decomp(self):
        return (not self.is_complete()) and (self.duration > self.sim.params.t_decomposition)
```

-   `JobFragment` is the most complex
    -   Duration is specified by its creator (part of the total time required by a regular job)
    -   And it has a reference to a placeholder that keeps track of undone fragments
-   When then fragment is completed, it checks to see if it is the last one in its group
    -   If so, it bumps the priority of the completed job to medium and puts it back in the coder's queue
    -   If not, it does nothing

```{.py data-file=decompose.py}
class JobFragment(Job):
    def __init__(self, coder, placeholder, duration):
        super().__init__(coder.sim, Priority.MEDIUM)
        self.coder = coder
        self.placeholder = placeholder
        self.duration = duration

    def complete(self):
        super().complete()
        self.placeholder.count -= 1
        if self.placeholder.count == 0:
            self.placeholder.job.complete()
            self.placeholder.job.priority = Priority.MEDIUM
            return self.coder.queue.put(self.placeholder.job)
        else:
            return self.sim.do_nothing()
```

-   When `.complete` wants to put the original (regular) job back in the coder's queue,
    it would be natural to call `yield self.code.queue.put(…)`
-   But what if it doesn't?
-   Solution:
    -   `.complete` always returns something that can be yielded
    -   Either "put this job in queue" *or* "wait for 0 ticks"

```{.py data-file=decompose.py}
class Simulation(Environment):
    def do_nothing(self):
        return self.timeout(0)
```

-   `Coder.run` gets a job from the general "new work" queue or from its priority queue
    -   Gives preference to the latter so that interrupts and fragments are done before regular work
    -   Always yields result of `job.complete()`

```{.py data-file=decompose.py}
    def run(self):
        while True:
            job = yield from self.get()
            job.start()
            if job.needs_decomp():
                yield from self.decompose(job)
            elif not job.is_complete():
                yield self.sim.timeout(job.duration)
                yield job.complete()
```

-   To decompose a job:
    -   Figure out the durations of the fragments
    -   Create a placeholder to keep track of them and the original job
    -   Put the fragments in the coder's priority queue

```{.py data-file=decompose.py}
    def decompose(self, job):
        size = self.sim.params.t_decomposition
        num = int(job.duration / size)
        extra = job.duration - (num * size)
        durations = [extra, *[size for _ in range(num)]]
        placeholder = Placeholder(job=job, count=len(durations))
        for d in durations:
            yield self.queue.put(JobFragment(self, placeholder, d))
```

-   So is this better than using interrupts?
    -   250 lines for decomposition vs. 212 for interrupts
    -   Decomposition approach was simpler to debug
    -   But tracking sub-jobs is harder
