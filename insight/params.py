from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
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
