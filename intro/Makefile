SRC=$(wildcard *.py)
OUT=$(patsubst %.py,%.out,${SRC})

all: ${OUT}

%.out: %.py
	-python $< >& $@
