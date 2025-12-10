all: \
  fixed_work_and_break.out \
  uniform_work_and_break.out \
  monitor_uniform_work_and_break.out \
  plot_log_normal.svg

%.out: %.py
	python $< >& $@

%.svg: %.py
	python $< $@
