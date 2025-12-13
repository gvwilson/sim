"""Using a generator in a loop."""

def gen_char_from_string(text):
    for ch in text:
        yield ch


characters = [ch for ch in gen_char_from_string("two")]
print(f"result as list: {characters}")
