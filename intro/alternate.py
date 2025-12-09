def alternate(processes):
    while True:
        try:
            for proc in processes:
                yield next(proc)
        except StopIteration:
            break

def seq(values):
    for v in values:
        yield v

sequences = [seq("ab"), seq("123")]
for thing in alternate(sequences):
    print(thing)
