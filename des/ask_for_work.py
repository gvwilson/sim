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
