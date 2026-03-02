"""Ask for work at regular intervals."""

from asimpy import Environment, Process

T_SIM = 30
T_WAIT = 8


class Coder(Process):
    def init(self):
        self.sim = self._env

    async def run(self):
        while True:
            print(f"{self.sim.now}: Is there any work?")
            await self.timeout(T_WAIT)


if __name__ == "__main__":
    env = Environment()
    Coder(env)
    env.run(until=T_SIM)
