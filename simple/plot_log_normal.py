import numpy as np
import plotly.express as px
import polars as pl
from scipy.stats import lognorm
import sys

mu = 0.25
sigma = 0.5

dist = lognorm(s=sigma, scale=np.exp(mu))
x = np.linspace(dist.ppf(0.001), dist.ppf(0.99), 500)
y = dist.pdf(x)

df = pl.DataFrame({"x": x, "y": y})
fig = px.line(df, x="x", y="y")
fig.write_image(sys.argv[1])
