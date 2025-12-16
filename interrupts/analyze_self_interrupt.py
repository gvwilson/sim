import plotly.express as px
import polars as pl
import sys

data = [
    {"arrival": 5.0, "n_prog": 1, "n_interrupt": 0, "count": 1100},
    {"arrival": 5.0, "n_prog": 1, "n_interrupt": 1, "count": 79},
    {"arrival": 5.0, "n_prog": 1, "n_interrupt": 2, "count": 36},
    {"arrival": 5.0, "n_prog": 1, "n_interrupt": 3, "count": 9},
    {"arrival": 5.0, "n_prog": 1, "n_interrupt": 4, "count": 5},
    {"arrival": 5.0, "n_prog": 2, "n_interrupt": 0, "count": 1060},
    {"arrival": 5.0, "n_prog": 2, "n_interrupt": 1, "count": 143},
    {"arrival": 5.0, "n_prog": 2, "n_interrupt": 2, "count": 23},
    {"arrival": 5.0, "n_prog": 2, "n_interrupt": 3, "count": 3},
    {"arrival": 5.0, "n_prog": 3, "n_interrupt": 0, "count": 1038},
    {"arrival": 5.0, "n_prog": 3, "n_interrupt": 1, "count": 167},
    {"arrival": 5.0, "n_prog": 3, "n_interrupt": 2, "count": 23},
    {"arrival": 5.0, "n_prog": 3, "n_interrupt": 3, "count": 2},
    {"arrival": 2.5, "n_prog": 1, "n_interrupt": 0, "count": 1078},
    {"arrival": 2.5, "n_prog": 1, "n_interrupt": 1, "count": 285},
    {"arrival": 2.5, "n_prog": 1, "n_interrupt": 2, "count": 38},
    {"arrival": 2.5, "n_prog": 1, "n_interrupt": 3, "count": 6},
    {"arrival": 2.5, "n_prog": 1, "n_interrupt": 4, "count": 1},
    {"arrival": 2.5, "n_prog": 2, "n_interrupt": 0, "count": 1153},
    {"arrival": 2.5, "n_prog": 2, "n_interrupt": 1, "count": 167},
    {"arrival": 2.5, "n_prog": 2, "n_interrupt": 2, "count": 60},
    {"arrival": 2.5, "n_prog": 2, "n_interrupt": 3, "count": 19},
    {"arrival": 2.5, "n_prog": 2, "n_interrupt": 4, "count": 7},
    {"arrival": 2.5, "n_prog": 2, "n_interrupt": 5, "count": 1},
    {"arrival": 2.5, "n_prog": 2, "n_interrupt": 6, "count": 1},
    {"arrival": 2.5, "n_prog": 3, "n_interrupt": 0, "count": 1084},
    {"arrival": 2.5, "n_prog": 3, "n_interrupt": 1, "count": 221},
    {"arrival": 2.5, "n_prog": 3, "n_interrupt": 2, "count": 59},
    {"arrival": 2.5, "n_prog": 3, "n_interrupt": 3, "count": 11},
    {"arrival": 2.5, "n_prog": 3, "n_interrupt": 4, "count": 0},
    {"arrival": 2.5, "n_prog": 3, "n_interrupt": 5, "count": 0},
    {"arrival": 2.5, "n_prog": 3, "n_interrupt": 6, "count": 1},
]
df = pl.from_dicts(data).sort("arrival")

fig = px.bar(df, x="n_interrupt", y="count", facet_row="n_prog", facet_col="arrival")
fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
if len(sys.argv) == 1:
    fig.show()
else:
    fig.write_image(sys.argv[1])
