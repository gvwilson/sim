"""Analyze corrected interruption simulation."""

import json
import plotly.express as px
import polars as pl
import sys

def main():
    df = pl.from_dicts(json.load(sys.stdin)["jobs"])

    regular = df.filter(pl.col("kind") == "regular")
    num_regular = regular.height
    num_regular_started = regular.filter(pl.col("t_start").is_not_null()).height
    num_regular_completed = regular.filter(pl.col("t_end").is_not_null()).height
    print(f"num_regular: {num_regular}")
    print(f"num_regular_started: {num_regular_started}")
    print(f"num_regular_completed: {num_regular_completed}")

    interrupt = df.filter(pl.col("kind") == "interrupt")
    num_interrupt = interrupt.height
    num_interrupt_started = interrupt.filter(pl.col("t_start").is_not_null()).height
    num_interrupt_completed = interrupt.filter(pl.col("t_end").is_not_null()).height
    print(f"num_interrupt: {num_interrupt}")
    print(f"num_interrupt_started: {num_interrupt_started}")
    print(f"num_interrupt_completed: {num_interrupt_completed}")

if __name__ == "__main__":
    main()
