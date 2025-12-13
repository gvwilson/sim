all: \
  strict_priorities.svg \
  weighted_priorities_200.svg \
  weighted_priorities_1000.svg \
  weighted_triage_1000.svg \
  weighted_triage_completion_1001.svg

strict_priorities.svg: analyze_queue_length.py strict_priorities.py
	python $(word 2, $^) | python $< $@

weighted_priorities_200.svg: analyze_queue_length.py weighted_priorities.py
	python $(word 2, $^) --overrides t_sim=200 | python $< $@

weighted_priorities_1000.svg: analyze_queue_length.py weighted_priorities.py
	python $(word 2, $^) --overrides t_sim=1000 | python $< $@

weighted_triage_1000.svg: analyze_queue_length.py weighted_triage.py
	python $(word 2, $^) --overrides t_sim=1000 | python $< $@

weighted_triage_completion_1001.svg: analyze_completed_triaged.py weighted_triage.py
	python $(word 2, $^) --overrides t_sim=1001 | python $< $@

clean:
	@rm -f *~ *.svg
