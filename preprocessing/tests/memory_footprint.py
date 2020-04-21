import sys
import decimal

d = {
    "int": 0,
    "float": 0.0,
    "dict": dict(),
    "set": set(),
    "tuple": tuple(),
    "list": list(),
    "str": "a",
    "unicode": u"a",
    "decimal": decimal.Decimal(0),
    "object": object(),
}
for k, v in sorted(d.items()):
    print(k, sys.getsizeof(v))