# Runnable tasks.

NOT_SIMULATIONS=__init__ sim util
SIMULATIONS=$(filter-out ${NOT_SIMULATIONS},$(patsubst sim/%.py,%,$(wildcard sim/*.py)))

all: commands

## commands: show available commands (*)
commands:
	@grep -h -E '^##' ${MAKEFILE_LIST} \
	| sed -e 's/## //g' \
	| column -t -s ':'

## check: check code
check:
	@ruff check .

## clean: clean up
clean:
	@find . -type f -name '*~' -exec rm {} \;
	@find . -type d -name __pycache__ | xargs rm -r
	@find . -type d -name .pytest_cache | xargs rm -r
	@find . -type d -name .ruff_cache | xargs rm -r

## format: format code
format:
	@ruff format .

## individual: test each simulation individually
individual:
	@for stem in ${SIMULATIONS}; do \
	  echo "========" $${stem}; \
	  python sim/sim.py --scenario $${stem} --params params/$${stem}.json; \
	done

## fig/summary_statistics.svg: generate histogram of summary statistics
fig/summary_statistics.svg: sim/summary_statistics.py sim/util.py sim/summary_statistics_plot.py params/summary_statistics_long.json
	@mkdir -p fig tmp
	@python sim/sim.py --scenario summary_statistics --params params/summary_statistics_long.json > tmp/summary_statistics_long.csv
	@python sim/summary_statistics_plot.py tmp/summary_statistics_long.csv $@
