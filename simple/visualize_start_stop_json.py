"""Visualize job start and stop times produced by monitor_uniform_work_and_break.py."""

import json
import plotly.express as px
import polars as pl
import sys

df = pl.from_dicts(json.load(sys.stdin)).with_columns(
    pl.when(pl.col("event") == "start").then(1).otherwise(-1).alias("delta")
)
events = df.with_columns(pl.col("delta").cum_sum().alias("state"))

fig = px.line(events, x="time", y="state", line_shape="hv")
fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}).update_yaxes(tickvals=[0, 1])
fig.write_image(sys.argv[1])
