"""Analyze queue lengths produced by queue_lengths.py."""

import json
import plotly.express as px
import polars as pl
import sys

data = json.load(sys.stdin)
temp = []
for record in data:
    temp.append(
        pl.from_dicts(record["lengths"]) \
          .with_columns(pl.lit(record["params"]["t_job_arrival"]).alias("arrival"))
    )
df = pl.concat(temp)

fig = px.line(df, x="time", y="length", color="arrival")
fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
if len(sys.argv) == 1:
    fig.show()
else:
    fig.write_image(sys.argv[1])
