"""Sending data into a generator."""

def gen_upper_lower(text):
    lower = True
    i = 0
    while i < len(text):
        result = text[i]
        i += 1
        temp = result.lower() if lower else result.upper()
        lower = yield temp


vowels = "aeiou"
generator = gen_upper_lower("abcdefg")
ch = next(generator)
while True:
    print(ch)
    flag = ch in vowels
    try:
        ch = generator.send(flag)
    except StopIteration:
        break
