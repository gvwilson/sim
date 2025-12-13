"""Analyze simulation of multiple programmers sharing a single queue."""

import json
import polars as pl
from prettytable import PrettyTable, TableStyle
import sys

PREC = 3

data = json.load(sys.stdin)
params = data["params"]
jobs = data["jobs"]
table = PrettyTable()
table.field_names = ["result", "value"]
table.align["result"] = "l"
table.align["value"] = "r"

df = pl.from_dicts(jobs) \
       .sort("id") \
       .with_columns((pl.col("t_end") - pl.col("t_start")).alias("t_job"))

# Mean inter-job arrival time
mean_arrival_time = df \
    .with_columns(pl.col("t_create").diff().alias("diff")) \
    .drop_nulls("diff") \
    .select(pl.col("diff").mean()) \
    .item()
table.add_row(["mean inter-job arrival time", round(mean_arrival_time, 3)])

# Mean job execution time
mean_job_time = df \
    .drop_nulls("t_end") \
    .select(pl.col("t_job").mean()) \
    .item()
table.add_row(["mean job execution time", round(mean_job_time, 3)])

# Programmer utilization
utilization = (df.drop_nulls("t_end").height * mean_job_time) / (params["t_sim"] * params["n_programmer"])
table.add_row(["utilization", round(utilization, PREC)])

# Display
table.set_style(TableStyle.MARKDOWN)
print(table)
