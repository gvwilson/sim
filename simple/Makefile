all: \
  fixed_work_and_break.out \
  uniform_work_and_break.out \
  plot_log_normal.svg \
  visualize_uniform_work_and_break.svg \
  simulate_with_objects.out \
  visualize_sampling_log.svg

%.out: %.py
	python $< >& $@

%.json: %.py
	python $< >& $@

plot_log_normal.svg: plot_log_normal.py
	python $< $@

visualize_uniform_work_and_break.svg: visualize_start_stop_json.py monitor_uniform_work_and_break.json
	cat $(word 2, $^) | python $< $@

visualize_sampling_log.svg: visualize_sampling_log.py sampling_log.json
	cat $(word 2, $^) | python $< $@
