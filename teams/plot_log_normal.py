"""Plog the log-normal distribution."""

import numpy as np
import plotly.express as px
import polars as pl
from scipy.stats import lognorm
import sys

mu = 0.5
sigma = 0.6

dist = lognorm(s=sigma, scale=np.exp(mu))
x = np.linspace(dist.ppf(0.001), dist.ppf(0.99), 500)
y = dist.pdf(x)

df = pl.DataFrame({"x": x, "y": y})
fig = px.line(df, x="x", y="y")
fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})
fig.write_image(sys.argv[1])
