from dataclasses import dataclass, field
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Params:
    n_coders: int = field(default=2, metadata={"doc": "number of coders"})
    n_iter: int = field(default=1, metadata={"doc": "number of simulations"})
    n_seed: int = field(default=97531, metadata={"doc": "RNG seed"})
    n_testers: int = field(default=2, metadata={"doc": "number of testers"})
    p_rework: float = field(default=0.5, metadata={"doc": "probability of job rework"})
    t_code_arrival: float = field(default=2.0, metadata={"doc": "job arrival rate"})
    t_code_mean: float = field(default=0.5, metadata={"doc": "mean code completion time"})
    t_code_std: float = field(default=0.6, metadata={"doc": "st. dev. code completion time"})
    t_integration: float = field(default=0.2, metadata={"doc": "post-work integration time"})
    t_interrupt_arrival: float = field(default=5.0, metadata={"doc": "interrupt arrival rate"})
    t_interrupt_mean: float = field(default=0.2, metadata={"doc": "mean interrupt time"})
    t_interrupt_std: float = field(default=0.1, metadata={"doc": "std. dev. interrupt time"})
    t_queue_monitor: float = field(default=5.0, metadata={"doc": "time between monitoring checks"})
    t_sim: float = field(default=20, metadata={"doc": "simulation length"})
