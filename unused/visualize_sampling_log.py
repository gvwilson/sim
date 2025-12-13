import json
import plotly.express as px
import polars as pl
import sys

df = pl.from_dicts(json.load(sys.stdin)).with_columns(
    pl.when(pl.col("state") == "work").then(1).otherwise(0).alias("state")
)

fig = px.line(df, x="time", y="state")
fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}).update_yaxes(tickvals=[0, 1])
fig.write_image(sys.argv[1])
