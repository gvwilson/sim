all: \
  plot_exponential.svg \
  plot_log_normal.svg \
  multiple_programmers.json \
  analyze_queue_lengths.svg \
  analyze_queue_lengths_zoom.svg

%.json: %.py
	python $< >& $@

%.svg: %.py
	python $< $@

analyze_queue_lengths.svg: analyze_queue_lengths.py queue_lengths.py
	python $(word 2, $^) --overrides t_sim=1000 --arrivals 0.6 0.8 1.0 1.2 | python $< $@

analyze_queue_lengths_zoom.svg: analyze_queue_lengths.py queue_lengths.py
	python $(word 2, $^) --overrides t_sim=1000 --arrivals 0.64 0.65 0.66 | python $< $@

clean:
	@rm -f *~ *.json *.svg
