def gen_upper_lower(text):
    lower = True
    i = 0
    while i < len(text):
        result = text[i]
        i += 1
        temp = result.lower() if lower else result.upper()
        lower = (yield temp)


vowels = "aeiou"
generator = gen_upper_lower("abcdefg")
for ch in generator:
    print(ch)
    flag = ch in vowels
    ch = generator.send(flag)
