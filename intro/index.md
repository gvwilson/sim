# Introduction

-   FIXME

## Learner Profile

-   Shae, 20, is starting the third year of an undergraduate degree in computer science
    after doing a one-semester work placement at a local mobile application development company.
-   Shae is comfortable with object-oriented programming in Python,
    and did well in their introductory courses on databases and web programming.
    They like working on homework assignments with friends,
    but had a bad experience in the team project in the web programming class.
    They use VS Code and Claude,
    but still mostly debug with print statements.
-   Shae found their work placement exciting because they got to work on real problems,
    but bewildering because they felt they spent more time in meetings than they did doing "real" work.
    They also heard senior programmers arguing about whether AI is a boon or a curse,
    and would like to know how to answer questions like that.
-   Shae is impatient with abstract theory;
    they learn best when generalizing from practical examples.

> These lessons teach Shae how to think analytically about software development processes,
> how to model and analyze those processes,
> and how to distinguish evidence-based claims from plausible punditry.

## Generators

-   A [generator](g:generator) is a function that returns a [lazy](g:lazy) [iterator](g:iterator)

-   Do all the steps manually

```{.python data-file=char_from_string.py}
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
```
```{.out data-file=char_from_string.out}
0: o
1: n
2: e
ended by exception
```

-   How we'd actually write it

```{.python data-file=char_with_loop.py}
def gen_char_from_string(text):
    for ch in text:
        yield ch


characters = [ch for ch in gen_char_from_string("two")]
print(f"result as list: {characters}")
```
```{.out data-file=char_with_loop.out}
result as list: ['t', 'w', 'o']
```

-   Would otherwise use an object with state, but generators use the stack as state

```{.python data-file=infinite.py}
def gen_infinite(text):
    pos = 0
    while True:
        yield text[pos]
        pos = (pos + 1) % len(text)


for (i, ch) in enumerate(gen_infinite("three")):
    if i > 9:
        break
    print(i, ch)
```
```{.out data-file=infinite.out}
0 t
1 h
2 r
3 e
4 e
5 t
6 h
7 r
8 e
9 e
```

-   Something that can't easily be done any other way

```{.python data-file=combinations.py}
def gen_combinations(left, right):
    for left_item in left:
        for right_item in right:
            yield (left_item, right_item)


for pair in gen_combinations("abc", [1, 2, 3]):
    print(pair)
```
```{.out data-file=combinations.out}
('a', 1)
('a', 2)
('a', 3)
('b', 1)
('b', 2)
('b', 3)
('c', 1)
('c', 2)
('c', 3)
```

-   Injecting values into a generator (which we need for simulations)

```{.python data-file=send.py}
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
ch = next(generator)
while True:
    print(ch)
    flag = ch in vowels
    try:
        ch = generator.send(flag)
    except StopIteration:
        break
```
```{.out data-file=send.out}
a
b
C
D
E
F
G
```

## Exercises

1.  Write a generator that produces items alternately from two lists.
1.  Write a generator that produces the average of the most recent N items in a list (sliding window average).
1.  Use `yield from` to generate a flat list from arbitrary nested lists.
1.  Explain why `gen/send_buggy.py` doesn't work.

```{.python data-file=send_buggy.py}
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
```
```{.out data-file=send_buggy.out}
a
C
E
G
Traceback (most recent call last):
  File "/Users/gvwilson/sim/intro/send_buggy.py", line 16, in <module>
    ch = generator.send(flag)
StopIteration
```
