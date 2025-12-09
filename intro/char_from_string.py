def gen_char_from_string(text):
    i = 0
    while i < len(text):
        yield text[i]
        i += 1


gen = gen_char_from_string("one")
try:
    i = 0
    while True:
        ch = next(gen)
        print(f"{i}: {ch}")
        i += 1
except StopIteration:
    print("ended by exception")
