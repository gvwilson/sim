all: \
  strict_priorities.svg \
  weighted_priorities_200.svg \
  weighted_priorities_1000.svg \

strict_priorities.svg: analyze_queue_length.py strict_priorities.py
	python $(word 2, $^) | python $< $@

weighted_priorities_200.svg: analyze_queue_length.py weighted_priorities.py
	python $(word 2, $^) --overrides t_sim=200 | python $< $@

weighted_priorities_1000.svg: analyze_queue_length.py weighted_priorities.py
	python $(word 2, $^) --overrides t_sim=1000 | python $< $@

clean:
	@rm -f *~ *.svg
