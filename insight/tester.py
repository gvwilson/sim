from actor import Actor
from jobs import JobIntegration


class Tester(Actor):
    def run(self):
        while True:
            self.log("waiting")
            job = yield self.sim.test_queue.get()
            job.tester_id = self.id
            job.log("testing")
            self.log("working")
            yield self.sim.timeout(job.t_test)
            self.log("done")
            if job.needs_rework():
                job.log("wait_rework")
                yield self.sim.coders[job.coder_id].queue.put(job)
            elif job.needs_integration():
                job.log("complete")
                for coder in self.sim.coders:
                    yield coder.queue.put(JobIntegration(job))
