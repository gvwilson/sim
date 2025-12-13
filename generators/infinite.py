"""Infinite generator."""

def gen_infinite(text):
    pos = 0
    while True:
        yield text[pos]
        pos = (pos + 1) % len(text)


for i, ch in enumerate(gen_infinite("three")):
    if i > 9:
        break
    print(i, ch)
