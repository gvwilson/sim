from dataclasses import dataclass, field
from simpy import Environment


@dataclass
class Log:
    env: Environment | None = None
    queue_events: list = field(default_factory=list)
    actor_events: list = field(default_factory=list)

    def actor(self, kind, id, state):
        self.actor_events.append(
            {"time": self.env.now, "kind": kind, "id": id, "state": state}
        )

    def queue(self, name, length):
        self.queue_events.append({"time": self.env.now, "name": name, "length": length})
