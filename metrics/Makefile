FOUR_METRICS = \
  four_metrics_backlog.svg \
  four_metrics_delay.svg \
  four_metrics_throughput_utilization.txt

JOB_ARRIVAL_NARROW = \
  job_arrival_narrow.svg \
  job_arrival_narrow.txt

JOB_ARRIVAL_WIDE = \
  job_arrival_wide.svg \
  job_arrival_wide.txt

TARGETS = \
  measure_delay.txt \
  measure_delay_sweep.svg \
  ${FOUR_METRICS} \
  ${JOB_ARRIVAL_NARROW} \
  ${JOB_ARRIVAL_WIDE}

all: ${TARGETS}

measure_delay.txt: measure_delay.py
	python $< --tables > $@

measure_delay_sweep.svg: measure_delay.py
	python measure_delay.py \
	--figure measure_delay_sweep.svg \
	-- t_sim=100,500,1000

${FOUR_METRICS}: four_metrics.py
	python four_metrics.py \
	--figure four_metrics_backlog.svg four_metrics_delay.svg \
	-- t_sim=200,200,1000,1000 \
	> four_metrics_throughput_utilization.txt

${JOB_ARRIVAL_NARROW}: job_arrival.py
	python job_arrival.py \
	--figure job_arrival_narrow.svg \
	--table \
	t_job_interval=1.0,1.1,1.2,1.3,1.4,1.5,1.6,1.7,1.8,1.9,2.0 t_sim=200 \
	> job_arrival_narrow.txt

${JOB_ARRIVAL_WIDE}: job_arrival.py
	python job_arrival.py \
	--figure job_arrival_wide.svg \
	--table \
	t_job_interval=0.5,1.0,2.0,3.0,4.0 t_sim=200 \
	> job_arrival_wide.txt

clean:
	@rm -rf *~ __pycache__

sterile: clean
	@rm -f ${TARGETS}
