"""Entry point."""

import argparse
import importlib
import random
import sys


SCENARIOS = [
    "independent_fixed_work",
    "independent_random_work",
    "task_queue_developer_process",
    "developer_pool_task_process",
    "developer_pool_variable_speed",
    "two_stage_no_coordination",
]


def main():
    args = _parse_args()

    if args.seed is not None:
        random.seed(args.seed)

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
            module.main(args)
        except ImportError as exc:
            print(exc, file=sys.stderr)
            sys.exit(1)


def _parse_args():
    """Handle command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="run all scenarios")
    parser.add_argument(
        "--scenario", choices=SCENARIOS, required=True, help="scenario to run"
    )
    parser.add_argument("--seed", type=int, help="RNG seed")
    parser.add_argument("--verbose", type=int, default=0, help="logging level")
    return parser.parse_args()


if __name__ == "__main__":
    main()
