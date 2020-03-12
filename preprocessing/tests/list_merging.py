import itertools
import timeit

def flattenListOfLists(lst):
    result = []
    for sublist in lst:
        result.extend(sublist)
    return result

def flattenListOfLists2(lst):
    result = []
    [result.extend(sublist) for sublist in lst]  # uggly side effect ;)
    return result

def flattenIterTools(lst):
    return list(itertools.chain(*lst))


a = ["a",   "i",   "u",   "e",   "o"]
k = ["ka",  "ki",  "ku",  "ke",  "ko"]
g = ["ga",  "gi",  "gu",  "ge",  "go"]
s = ["sa",  "shi", "su",  "se",  "so"]
z = ["za",  "ji",  "zu",  "ze",  "zo"]
t = ["ta",  "chi", "tsu", "te",  "to"]
d = ["da",         "du",  "de",  "do"]
n = ["na",  "ni",  "nu",  "ne",  "no"]
h = ["ha",  "hi",  "hu",  "he",  "ho"]
b = ["ba",  "bi",  "bu",  "be",  "bo"]
p = ["pa",  "pi",  "pu",  "pe",  "po"]
m = ["ma",  "mi",  "mu",  "me",  "mo"]
y = ["ya",         "yu",         "yo"]
n = ["n"]

kana = [a, k, g, s, z, t, d, n, h, b, p, m, y, n]

t = timeit.timeit('lst = flattenListOfLists(kana)', 'from __main__ import kana, flattenListOfLists', number=100000)
print('for loop:', t)

t = timeit.timeit('lst = flattenListOfLists2(kana)', 'from __main__ import kana, flattenListOfLists2', number=100000)
print('list comprehension side effect:', t)

t = timeit.timeit('lst = flattenIterTools(kana)', 'from __main__ import kana, flattenIterTools\nimport itertools', number=100000)
print('itertools:', t)