"""Entry point."""

import argparse
import importlib
import random
import sys


SCENARIOS = [
    "independent_fixed_work",
    "independent_random_work",
    "task_queue_worker_process",
    "worker_pool_task_process",
    "worker_pool_variable_speed",
]


def main():
    args = _parse_args()

    if args.scenario is None:
        print("missing required argument --scenario [name]", file=sys.stderr)
        sys.exit(1)

    if args.seed is not None:
        random.seed(args.seed)

    try:
        module = importlib.import_module(args.scenario)
        module.main(args)
    except ImportError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)


def _parse_args():
    """Handle command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--scenario", choices=SCENARIOS, required=True, help="scenario to run"
    )
    parser.add_argument("--seed", type=int, help="RNG seed")
    parser.add_argument("--verbose", type=int, default=0, help="logging level")
    return parser.parse_args()


if __name__ == "__main__":
    main()
