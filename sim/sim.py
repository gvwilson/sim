"""Entry point."""

import argparse
import importlib
import json
import random
import sys


SCENARIOS = [
    "independent_fixed_work",
    "independent_random_work",
    "task_queue_developer_process",
    "developer_pool_task_process",
    "developer_pool_variable_speed",
    "two_stage_no_coordination",
    "two_stage_with_coordination",
    "two_stage_with_rework",
    "two_stage_refactored",
    "two_stage_logging",
    "summary_statistics",
    "self_recording",
    "independent_fixed_work_self_recording",
]

PARAMETERS = {
    "num_developers": 3,
    "num_testers": 2,
    "simulation_duration": 30,
    "task_arrival_rate": 4,
    "max_task_duration": 5,
    "max_developer_speed": 4,
    "max_tester_speed": 3,
    "handoff_fraction": 0.1,
    "rework_fraction": 0.6,
    "seed": 67890
}


def main():
    args = _parse_args()
    params = _load_parameters(args)
    random.seed(params["seed"])

    if args.all:
        scenarios = SCENARIOS
    elif args.scenario is None:
        print("no scenario specified (use --scenario [name])", file=sys.stderr)
        sys.exit(1)
    else:
        scenarios = [args.scenario]

    for sc in scenarios:
        try:
            module = importlib.import_module(sc)
            module.main(params)
        except ImportError as exc:
            print(exc, file=sys.stderr)
            sys.exit(1)


def _load_parameters(args):
    """Get simulation parameters."""
    params = PARAMETERS.copy()
    if args.params is not None:
        with open(args.params, "r") as reader:
            params.update(json.load(reader))
    return params


def _parse_args():
    """Handle command-line arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="run all scenarios")
    parser.add_argument("--params", type=str, help="parameter file")
    parser.add_argument("--scenario", choices=SCENARIOS, help="scenario to run")
    parser.add_argument("--verbose", type=int, default=0, help="logging level")
    return parser.parse_args()


if __name__ == "__main__":
    main()
