"""Utilities."""

import argparse
from itertools import product
import polars as pl
import random
import sys

PRECISION = 2


def as_frames(results):
    """Convert JSON to dataframes."""

    for i, res in enumerate(results):
        for key in res:
            if key == "params":
                continue
            res[key] = pl.from_dicts(res[key])
            res[key] = res[key].with_columns(pl.lit(i).alias("iter"))
            for name, value in res["params"].items():
                res[key] = res[key].with_columns(pl.lit(value).alias(name))

    frames = {}
    for key in results[0]:
        if key == "params":
            continue
        frames[key] = pl.concat(r[key] for r in results)

    return frames


def df_smooth(df, col_by, col_ave):
    result = df.group_by(col_by).agg(pl.col(col_ave).mean().alias(col_ave)).sort(col_by)
    return result


def df_jobs(jobs):
    return (
        jobs.filter(pl.col("t_start").is_not_null())
        .sort("t_create")
        .with_columns((pl.col("t_start") - pl.col("t_create")).alias("delay"))
    )


def df_throughput(jobs, group_col="iter"):
    return (
        df_jobs(jobs)
        .filter(pl.col("t_complete").is_not_null())
        .group_by(group_col)
        .agg(
            [
                pl.col("t_sim").first(),
                pl.len().alias("num_jobs"),
            ]
        )
        .with_columns(
            (pl.col("num_jobs") / pl.col("t_sim")).round(PRECISION).alias("throughput")
        )
        .sort(group_col)
    )


def df_utilization(coders, group_col="iter"):
    return (
        coders.group_by(group_col)
        .agg(
            [
                pl.col("t_sim").first(),
                pl.len().alias("count"),
                pl.col("t_work").sum().alias("total_work"),
            ]
        )
        .with_columns(
            (pl.col("total_work") / (pl.col("count") * pl.col("t_sim")))
            .round(PRECISION)
            .alias("utilization")
        )
        .drop("count")
    )


def rnd(obj, key=None):
    """Round non-null floating point values."""
    value = obj if key is None else getattr(obj, key)
    return round(value, PRECISION) if isinstance(value, float) else value


def run(params_cls, simulation_cls):
    """Run simulation for each combination of parameters."""

    args, params, options = _parse_args(params_cls)
    if args.params:
        _show_params(params_cls)
        sys.exit(0)

    random.seed(params.n_seed)
    scenarios = _create_scenarios(params, options)

    results = []
    for scenario in scenarios:
        sim = _create_simulation(simulation_cls, scenario)
        sim.simulate()
        results.append({"params": sim.params.to_dict(), **sim.result()})

    return args, results


def show_frames(frames, without):
    with pl.Config(
        tbl_formatting="MARKDOWN",
        tbl_hide_column_data_types=True,
        tbl_hide_dataframe_shape=True,
        tbl_rows=-1,
    ):
        for name, df in frames.items():
            print(f"## {name}")
            print(df.select(pl.exclude(without)))


def _show_params(params_cls):
    known = params_cls.__dataclass_fields__
    for key, value in sorted(known.items()):
        print(f"{key} ({value.default}): {value.metadata.get("doc", "---")}")


def show_through_util(throughput, utilization):
    with pl.Config(
        tbl_formatting="MARKDOWN",
        tbl_hide_column_data_types=True,
        tbl_hide_dataframe_shape=True,
        tbl_rows=-1,
    ):
        print("## throughput\n")
        print(throughput)
        print("\n## utilization\n")
        print(utilization)


def _create_scenarios(params, options):
    """Create all possible scenarios from parameters."""

    # Handle repeated iterations with the same parameters.
    if "n_iter" in options:
        assert len(options["n_iter"]) == 1, f"Invalid n_iter {options['n_iter']}"
        options["n_iter"] = list(range(int(options["n_iter"][0])))
    elif hasattr(params, "n_iter"):
        options["n_iter"] = list(range(params.n_iter))

    # Expand scenarios.
    keys = list(options.keys())
    values = list(options.values())
    scenarios = []
    for combination in product(*values):
        scenarios.append(dict(zip(keys, combination)))

    return scenarios


def _create_simulation(simulation_cls, scenario):
    """Create a simulation with one scenario's parameter values."""

    sim = simulation_cls()
    for key, value in scenario.items():
        assert hasattr(sim.params, key), f"unknown parameter key {key}"
        setattr(sim.params, key, value)
    return sim


def _parse_args(params_cls):
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--figure", nargs="+", help="figure file(s)")
    parser.add_argument("--json", action="store_true", help="show result as JSON")
    parser.add_argument("--params", action="store_true", help="explain parameters")
    parser.add_argument("--tables", action="store_true", help="show result as tables")
    args, overrides = parser.parse_known_args()

    params = params_cls()
    options = {}
    for arg in overrides:
        if arg == "--":
            continue
        fields = arg.split("=")
        assert len(fields) == 2, f"malformed parameter options {arg}"

        key, values = fields
        assert hasattr(params, key), f"unknown parameter key {key}"

        values = values.split(",")
        assert (len(values) > 0) and (all(len(v) > 0 for v in values)), (
            f"missing value(s) for parameter key {key}"
        )

        if isinstance(getattr(params, key), int):
            options[key] = [int(v) for v in values]
        elif isinstance(getattr(params, key), float):
            options[key] = [float(v) for v in values]
        else:
            options[key] = values

    return args, params, options
