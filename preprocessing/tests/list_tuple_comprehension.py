a = [
    [1, 2]
]
b = [tuple((d for d in c if d > 1)) for c in a]
print(b)
