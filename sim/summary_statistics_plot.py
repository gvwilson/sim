"""Plot histogram of task duration."""

import sys

import polars as pl
import plotly.express as px


df = pl.read_csv(sys.argv[1]).filter(pl.col("verb") == "elapsed")
fig = px.histogram(df, x="time")
fig.write_image(sys.argv[2])
