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

-   In asimpy, `Process` objects can be interrupted directly
    -   No need to store a separate process handle
    -   Coders are stored in a list so the interrupter can reach them

```{.py .python data-file=discard.py}
class Simulation(Environment):
    def simulate(self):
        # …queue and manager as before…
        Interrupter(self)

        self.coders = []
        for _ in range(self.params.n_coder):
            coder = Coder(self)
            self.coders.append(coder)

        self.run(until=self.params.t_sim)
```

-   `Interrupter` calls `.interrupt(cause)` directly on the `Process` object
    -   Pass `None` as the cause when there is no associated data

```{.py data-file=discard.py}
class Interrupter(Process):
    def init(self):
        self.sim = self._env
        # …recorder setup…

    async def run(self):
        while True:
            await self.timeout(self.sim.rand_interrupt_arrival())
            coder = random.choice(self.sim.coders)
            coder.interrupt(None)
```

<div class="callout" markdown="1">

-   When we call `process.interrupt(cause)`, asimpy raises an `Interrupt` exception inside the coroutine
-   But it can only do this while the framework is running, *not* while the process is running
    -   Because only one thing runs at a time
-   So the exception is only raised when the process interacts with the environment
    -   I.e., at `queue.get()`, `timeout()`, or other `await` points

</div>

-   Write a `Coder` that throws away whatever job it's doing when it is interrupted
    -   Not realistic, but it gives us a chance to learn about interrupts

```{.py data-file=discard.py}
from asimpy import Interrupt

class Coder(Process):
    def init(self):
        self.sim = self._env
        # …recorder setup…
        self.n_interrupt = 0
        self.t_work = 0

    async def run(self):
        while True:
            try:
                job = await self.sim.queue.get()
                job.t_start = self.sim.now
                await self.timeout(job.duration)
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
-   Note that `Interrupter` passes the new job directly to `.interrupt()` so that it becomes the exception's `.cause`

```{.py data-file=interrupts.py}
class Interrupter(Process):
    def init(self):
        self.sim = self._env
        # …recorder setup…

    async def run(self):
        while True:
            await self.timeout(self.sim.rand_interrupt_arrival())
            coder = random.choice(self.sim.coders)
            coder.interrupt(JobInterrupt(self.sim))
```

-   It took several tries to get the `Coder` right
-   The problem is that interrupts can occur whenever the coder interacts with asimpy
    -   So if the coder does anything with asimpy in the `except` block,
        we can have an interrupt while we're handling an interrupt
-   Solution is to implement a [state machine](g:state-machine)
    1.  No work, so get a new job from the coding queue.
    2.  Job on top of the stack is incomplete, so do some work.
    3.  Job on top of the stack is complete, so pop it.
-   If an interrupt occurs:
    -   Add some time to the current job *if we actually started it*
    -   Push the new job on the stack
    -   Note: the new job arrives as the `Interrupt` exception's `.cause`

```{.py data-file=interrupts.py}
class Coder(Process):
    def init(self):
        self.sim = self._env
        # …recorder setup…
        self.t_work = 0
        self.stack = []

    async def run(self):
        while True:
            started = None
            try:
                # No work in hand, so get a new job.
                if len(self.stack) == 0:
                    job = await self.sim.code_queue.get()
                    job.start()
                    self.stack.append(job)
                # Current job is incomplete, so try to finish it.
                elif self.stack[-1].done < self.stack[-1].duration:
                    job = self.stack[-1]
                    started = self.sim.now
                    await self.timeout(job.duration - job.done)
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
    -   Treat interrupts as high-priority jobs placed in the coder's personal queue
    -   Break regular jobs into short fragments so that interrupts are handled promptly (but not immediately)
-   Define three priorities:
    -   High: interrupt
    -   Medium: fragments of regular job
    -   Low: regular jobs

```{.py data-file=decomp.py}
class Priority:
    HIGH = 0
    MEDIUM = 1
    LOW = 2
```

-   Generic `Job` has a few [lifecycle methods](g:lifecycle-method) for child classes to override
    -   `Job.start` is called when work starts on a job
    -   `Job.complete` is called when the job is completed; returns a parent job to re-queue, or `None`
    -   `Job.is_complete` tells us whether the job has been completed or not
    -   `Job.needs_decomp` tells us whether the job needs to be decomposed

```{.py data-file=decomp.py}
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
        return None

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

```{.py data-file=decomp.py}
class JobInterrupt(Job):
    def __init__(self, sim):
        super().__init__(sim, Priority.HIGH)
        self.duration = self.sim.rand_interrupt_duration()
```

-   `JobRegular` overrides `.needs_decomp()`
    -   If this job isn't complete *and* the time required is greater than the decomposition threshold
    -   The latter parameter is another completely arbitrary number

```{.py data-file=decomp.py}
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
-   When the fragment is completed, it checks to see if it is the last one in its group
    -   If so, it bumps the priority of the completed job to medium and returns it to be re-queued
    -   If not, it returns `None`

```{.py data-file=decomp.py}
class JobFragment(Job):
    def __init__(self, coder, placeholder, duration):
        super().__init__(coder.sim, Priority.MEDIUM)
        self.coder = coder
        self.placeholder = placeholder
        self.duration = duration

    def complete(self):
        self.t_complete = self.sim.now
        self.placeholder.count -= 1
        if self.placeholder.count == 0:
            parent = self.placeholder.job
            parent.t_complete = self.sim.now
            parent.priority = Priority.MEDIUM
            return parent
        return None
```

-   When `.complete()` returns a parent job, the coder puts it back in the priority queue
-   The coder always `await`s the result explicitly — no need for a "do nothing" placeholder event

```{.py data-file=decomp.py}
    async def run(self):
        while True:
            job = await self.get()
            job.start()
            if job.needs_decomp():
                await self.decompose(job)
            elif not job.is_complete():
                await self.timeout(job.duration)
                parent = job.complete()
                if parent is not None:
                    await self.queue.put(parent)
                    self.notify_work()
```

-   Two-queue selection uses the notification pattern instead of `yield (event1 | event2)`
    -   Each coder holds a `_work_event` that producers trigger when adding to either queue
    -   The `get()` method checks queues synchronously before waiting

```{.py data-file=decomp.py}
    def notify_work(self):
        """Signal that work may be available."""
        if self._work_event is not None and not self._work_event._triggered:
            self._work_event.succeed()

    async def get(self):
        """Get next job, preferring personal priority queue over shared queue."""
        while True:
            if not self.queue.is_empty():
                return await self.queue.get()
            if not self.sim.code_queue.is_empty():
                return await self.sim.code_queue.get()
            self._work_event = Event(self.sim)
            await self._work_event
```

-   To decompose a job:
    -   Figure out the durations of the fragments
    -   Create a placeholder to keep track of them and the original job
    -   Put the fragments in the coder's priority queue

```{.py data-file=decomp.py}
    async def decompose(self, job):
        size = self.sim.params.t_decomposition
        num = int(job.duration / size)
        extra = job.duration - (num * size)
        durations = [extra, *[size for _ in range(num)]]
        placeholder = Placeholder(job=job, count=len(durations))
        for d in durations:
            await self.queue.put(JobFragment(self, placeholder, d))
        self.notify_work()
```

-   The interrupter puts high-priority jobs directly into the coder's personal queue
    -   No process-level interrupt needed

```{.py data-file=decomp.py}
class Interrupter(Process):
    def init(self):
        self.sim = self._env
        # …recorder setup…

    async def run(self):
        while True:
            await self.timeout(self.sim.rand_interrupt_arrival())
            coder = random.choice(self.sim.coders)
            await coder.queue.put(JobInterrupt(self.sim))
            coder.notify_work()
```

-   So is this better than using interrupts?
    -   250 lines for decomposition vs. 212 for interrupts
    -   Decomposition approach was simpler to debug
    -   But tracking sub-jobs is harder
