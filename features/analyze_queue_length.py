"""Analyze queue lengths produced by strict_priorities.py."""

import json
import plotly.express as px
import polars as pl
import sys

df = pl.from_dicts(json.load(sys.stdin)["lengths"])
fig = px.line(df, x="time", y="length", color="priority")
fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
if len(sys.argv) == 1:
    fig.show()
else:
    fig.write_image(sys.argv[1])
