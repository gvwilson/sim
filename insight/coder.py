from asimpy import Event, Interrupt, Queue

from actor import Actor


class Coder(Actor):
    def post_init(self):
        self.queue = Queue(self.sim, priority=True)
        self.stack = []
        self._work_event = None

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

    async def run(self):
        while True:
            started = None
            try:
                # No work in hand, so get a new job.
                if len(self.stack) == 0:
                    self.log("getting")
                    job = await self.get()
                    job.start()
                    self.stack.append(job)
                # Current job is complete.
                elif self.stack[-1].is_complete():
                    self.log("finishing")
                    job = self.stack.pop()
                # Current job is incomplete, so try to finish it.
                else:
                    self.log("working")
                    job = self.stack[-1]
                    started = self.sim.now
                    await self.timeout(job.t_code - job.t_code_done)
                    job.complete()

            except Interrupt as exc:
                self.log("interrupted")
                # Some work has been done on the current job, so save it.
                if (len(self.stack) > 0) and (started is not None):
                    job = self.stack[-1]
                    job.t_code_done += self.sim.now - started

                # Put the interrupting job on the stack.
                job = exc.cause
                job.start()
                self.stack.append(job)
