from simpy import Interrupt, PriorityStore

from actor import Actor


class Coder(Actor):
    def post_init(self):
        self.queue = PriorityStore(self.sim)
        self.stack = []

    def run(self):
        while True:
            started = None
            try:
                # No work in hand, so get a new job.
                if len(self.stack) == 0:
                    self.log("getting")
                    job = yield from self.get()
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
                    yield self.sim.timeout(job.t_code - job.t_code_done)
                    job.complete()

            except Interrupt as exc:
                self.log("interrupted")
                # Some work has been done on the current job, so save it.
                if (len(self.stack) > 0) and (started is not None):
                    job = self.stack[-1]
                    job.t_code_done += self.sim.now - started

                # Put the interrupting job on the stack.
                import sys
                job = exc.cause
                job.start()
                self.stack.append(job)

    def get(self):
        new_req = self.sim.code_queue.get()
        own_req = self.queue.get()
        result = yield (new_req | own_req)
        if (len(result.events) == 2) or (own_req in result):
            new_req.cancel()
            job = result[own_req]
        else:
            own_req.cancel()
            job = result[new_req]
        return job
