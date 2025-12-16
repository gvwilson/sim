all: \
  interrupt_resume.json \
  analyze_self_interrupt.svg

%.json: %.py
	python $< >& $@

%.svg: %.py
	python $< $@

clean:
	@rm -f *~ *.json
