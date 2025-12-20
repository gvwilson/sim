all: \
  analyze_simple_testing_queues.svg \
  analyze_simple_testing_times.svg \
  analyze_scenario_testing.svg

analyze_simple_testing_queues.svg analyze_simple_testing_times.svg: analyze_simple_testing.py simple_testing.py
	python $(word 2, $^) | python $< analyze_simple_testing_queues.svg analyze_simple_testing_times.svg

analyze_scenario_testing.svg: scenario_testing.py analyze_scenario_testing.py
	python scenario_testing.py | python analyze_scenario_testing.py $@

big_jobs_first.svg: big_jobs_first.py analyze_big_jobs_first.py
	python big_jobs_first.py | python analyze_big_jobs_first.py $@

clean:
	@rm -f *~ *.svg
