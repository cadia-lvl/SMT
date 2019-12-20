import re

IS_CHAR_LOWER = re.compile(r"[a-záðéíóúýþæö]")
IS_CHAR_UPPER = re.compile(r"[A-ZÁÐÉÍÓÚÝÞÆÖ]")
IS_COMBINE_NEWLINE = re.compile(r'([\w]+)\.\n([a-záðéíóúýþæö])')
IS_SPLIT_NEWLINE = re.compile(r'([\w\(\)\[\]\.]{2,})\.([A-ZÁÐÉÍÓÚÝÞÆÖ])')
URI = re.compile(r"((http(s)?:\/\/)|(www)|([-a-zA-Z0-9:%_\+.~#?&/=]+?@))+([-a-zA-Z0-9@:%_\+.~#?&/=]+)")
URI_SIMPLE = re.compile(r"([-a-zA-Z0-9@:%_\+.~#?&/=]+?)(\.is|\.com)")
EMPTY_BRACKETS = re.compile(r"[\[\(]\s*[\]\)]")
# u'\u007c' - |
PIPE = re.compile(r"\u007c")
# u'\u003c', u'\u003e' - <, >
LT = re.compile(r"\u003c")
GT = re.compile(r"\u003e")
# u'\u005b', u'\u005d' - [, ]
BRACKET_OPEN = re.compile(r"\u005b")
BRACKET_CLOSE = re.compile(r"\u005d")
FIX_PLACEHOLDERS = re.compile(r"_ (uri|gt|lt|pipe|bo|bc) _")
CRYLLIC = re.compile(r'.*[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F]+.*')
GREEK = re.compile(r'.*[\u0370-\u03bb\u03bd-\u03FF\u1F00-\u1FFF]+.*')
UNKNOWN_CHARS = re.compile(r'.*[žčšè¿ğūįł]+.*')
NOT_WORDS = re.compile(r'.*[\W\d_].*')

SUB_URI = {
    'pattern': URI,
    'repl': '_uri_'
}
SUB_URI_SIMPLE = {
    'pattern': URI_SIMPLE,
    'repl': '_uri_'
}
SUB_EMPTY_BRACKETS = {
    'pattern': EMPTY_BRACKETS,
    'repl': ''
}
SUB_PIPE = {
    'pattern': PIPE,
    'repl': '_pipe_'
}
SUB_FIX_PLACEHOLDERS = {
    'pattern': FIX_PLACEHOLDERS,
    'repl': r'_\1_'
}
SUB_LT = {
    'pattern': LT,
    'repl': '_lt_'
}
SUB_GT = {
    'pattern': GT,
    'repl': '_gt_'
}
SUB_BRACKET_OPEN = {
    'pattern': BRACKET_OPEN,
    'repl': '_bo_'
}
SUB_BRACKET_CLOSE = {
    'pattern': BRACKET_CLOSE,
    'repl': '_bc_'
}
SUB_IS_SPLIT_NEWLINE = {
    'pattern': IS_SPLIT_NEWLINE,
    'repl': r'\1. \2'
}
SUB_IS_COMBINE_NEWLINE = {
    'pattern': IS_COMBINE_NEWLINE,
    'repl': r'\1. \2'
}
