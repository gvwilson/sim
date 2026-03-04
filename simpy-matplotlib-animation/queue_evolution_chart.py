from itertools import count
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

plt.style.use("fivethirtyeight")

x_vals = []
y_vals = []

index = count()


def animate(i):
    data = pd.read_csv("data.csv")
    x = data["time"]
    y1 = data["queue_length"]

    plt.cla()

    plt.plot(x, y1, label="Queue evolution")

    plt.legend(loc="upper left")
    plt.tight_layout()


ani = FuncAnimation(plt.gcf(), animate, interval=1000)

plt.tight_layout()
plt.show()
