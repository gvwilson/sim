def gen_combinations(left, right):
    for left_item in left:
        for right_item in right:
            yield (left_item, right_item)


for pair in gen_combinations("abc", [1, 2, 3]):
    print(pair)
