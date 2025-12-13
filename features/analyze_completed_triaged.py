"""Analyze jobs completed and triaged."""

import json
import plotly.express as px
import polars as pl
import sys

def running_total(df, time_col, num_col, event):
    return df \
        .drop_nulls(time_col) \
        .sort(time_col) \
        .group_by(time_col) \
        .len() \
        .with_columns(pl.col("len").cum_sum().alias(num_col)) \
        .select(time_col, num_col) \
        .rename({time_col: "time", num_col: "count"}) \
        .with_columns(pl.lit(event).alias("event"))


def main():
    df = pl.from_dicts(json.load(sys.stdin)["jobs"], schema_overrides={"t_discard": pl.Float64})
    starts = running_total(df, "t_create", "n_create", "created")
    ends_high = running_total(df.filter(pl.col("priority") == 0), "t_end", "n_end", "completed_low")
    ends_low = running_total(df.filter(pl.col("priority") == 1), "t_end", "n_end", "completed_high")
    discards = running_total(df, "t_discard", "n_discard", "discarded")
    combined = pl.concat([starts, ends_high, ends_low, discards])

    fig = px.line(combined, x="time", y="count", color="event")
    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
    if len(sys.argv) == 1:
        fig.show()
    else:
        fig.write_image(sys.argv[1])


if __name__ == "__main__":
    main()
