#!/bin/bash

# Source - https://stackoverflow.com/a/68922466
# Posted by Sandy
# Retrieved 2026-01-11, License - CC BY-SA 4.0

uv run python simple_interaction_manager_coder.py &
uv run python queue_evolution_chart.py &
wait
