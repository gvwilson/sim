"""Analyze job statistics from job_object.py."""

import json
import plotly.express as px
import polars as pl
import sys

data = json.load(sys.stdin)

params = data["params"]
t_sim = params["t_sim"]

tasks = data["tasks"]
df = pl.from_dicts(tasks).pivot(index="id", on="event", values="time")
# df.show(tbl_formatting="MARKDOWN", limit=None, tbl_hide_column_data_types=True)

# Throughput
throughput = df.filter(pl.col("end").is_not_null()).height / t_sim
print(f"throughput: {throughput:.3f}")

# Delay
temp = df \
    .filter(pl.col("end").is_not_null()) \
    .with_columns((pl.col("end") - pl.col("created")).alias("elapsed"))
delay = temp["elapsed"].sum() / temp.height
print(f"delay: {delay:.3f}")

# Utilization
temp = df \
    .filter(pl.col("start").is_not_null()) \
    .with_columns(pl.col("end").fill_null(t_sim)) \
    .with_columns((pl.col("end") - pl.col("start")).alias("elapsed"))
utilization = temp["elapsed"].sum() / t_sim
print(f"utilization: {utilization:.3f}")
