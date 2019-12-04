"""
Sentence level processing. Some useful functions to process sentences.
"""
import re
from unicodedata import normalize
from typing import Tuple, List, Dict, Callable, \
    Sequence
from enum import Enum
from functools import partial

import tokenizer as mideind_tok
import nltk
# also in sacremoses: punct norm, detok and sent split
from sacremoses import MosesTokenizer

nltk.download('punkt')


class Lang(Enum):
    """An enum for supported ISO 639-1 language codes. String based"""
    EN = 'en'
    IS = 'is'


REGEXP_SUB: Dict[str, Tuple[re.Pattern, str]] = {
    # Taken from https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url?noredirect=1&lq=1
    'URI-OLD': (
        re.compile(
            r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'),
        '@uri@'),
    'IS-COMBINE-NEWLINE': (re.compile(r'([\w]+)\.\n([a-záðéíóúýþæö])'),
                           r'\1. \2'),
    'IS-SPLIT-NEWLINE': (re.compile(r'([\w\(\)\[\]\.]{2,})\.([A-ZÁÐÉÍÓÚÝÞÆÖ])'),
                         r'\1. \2'),
    'URI': (re.compile(
        r"((http(s)?:\/\/)|(www)|([-a-zA-Z0-9:%_\+.~#?&/=]+?@))+([-a-zA-Z0-9@:%_\+.~#?&/=]+)"),
            '@uri@'),
    'URI-SIMPLE': (re.compile(r"([-a-zA-Z0-9@:%_\+.~#?&/=]+?)(\.is|\.com)"), "@uri@"),
    'EMPTY-BRACKETS': (re.compile(r"[\[\(]\s*[\]\)]"), ""),
    # u'\u007c' - |
    'PIPE': (re.compile(r"\u007c"), '@pipe@'),
    # u'\u003c', u'\u003e' - <, >
    'LT': (re.compile(r"\u003c"), '@lt@'),
    'GT': (re.compile(r"\u003e"), '@gt@'),
    # u'\u005b', u'\u005d' - [, ]
    'BRACKET-OPEN': (re.compile(r"\u005b"), '@brac_open@'),
    'BRACKET-CLOSE': (re.compile(r"\u005d"), '@brac_close@'),
    'FIX-URI': (re.compile(r"@ uri @"), '@uri@'),
    'CRYLLIC': (re.compile(r'.*[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F]+.*'),
                ''),
    'GREEK': (re.compile(r'.*[\u0370-\u03bb\u03bd-\u03FF\u1F00-\u1FFF]+.*'), ''),
    'UNKNOWN-CHARS': (re.compile(r'.*[žčšè¿ğūįł]+.*'), ''),
    'NOT-WORDS': (re.compile(r'.*[\W\d_].*'), ''),
    'NOT-WORDS-OLD': (re.compile(r'.*[\d();.:,•\-=?!_+@].*'), '')
}


def regexp(sent: str, regexps: List[Tuple[re.Pattern, str]]) -> str:
    """
    Applies a list of regular expressions and their substitutions to a string.
    """
    processed_line = sent
    for regular_expression, sub_string in regexps:
        processed_line = re.sub(
            regular_expression, sub_string, processed_line)
    return processed_line


def lowercase_normalize(sent: str) -> str:
    """Applies unicode lowercase and normalize on a string."""
    return normalize('NFKC', sent.casefold())


def get_tokenizer(lang: Lang, method: str) -> Callable[[str], List[str]]:
    """
    Returns a tokenizer for a specified method and additional arguments.
    Supported methods:
        IS(default): "pass-through", basic tokenization.
        IS: "placeholders", uses placeholders for some NEs.
        EN(default): "moses", Moses tokenization, does not tackle URLs.
        Poor abbreviation handling.
        EN: "nltk", does not tackle URLs.
        EN: "toktok", handles URLs, does not handle "." but at the end.
    """
    if lang == Lang.EN:
        if method == "nltk":
            # We use the word_tokenize NLTL tokenizer for english
            return nltk.word_tokenize
        # o.w. we use Moses
        if method == 'toktok':
            toktok = nltk.tokenize.ToktokTokenizer()
            return toktok.tokenize
        m_tok = MosesTokenizer(lang='en')
        return partial(m_tok.tokenize, escape=False)
    # Moses for 'is'
    if method == 'moses':
        m_tok = MosesTokenizer(lang='is')
        return partial(m_tok.tokenize, escape=False)
    return partial(_tokenize_is, method=method)


def apply_tokenizer(sentence: str, tokenizer: Callable[[str], List[str]]) -> str:
    """Applies a tokenization function to a sentence."""
    return " ".join(tokenizer(sentence)) + "\n"


def tokenize(sentence: str, lang: Lang, method: str = 'pass-through'):
    """
    Tokenizes a sentence using the specified method. Returns the tokenized
    sentence.
    Supported methods:
        IS(default): "pass-through", basic tokenization.
        IS: "placeholders", uses placeholders for some NEs.
        EN(default): "moses", Moses tokenization, does not tackle URLs.
        Poor abbreviation handling.
        EN: "nltk", does not tackle URLs.
        EN: "toktok", handles URLs, does not handle "." but at the end.
    """
    tok = get_tokenizer(lang, method)
    return apply_tokenizer(sentence, tok)


def _tokenize_is(sentence: str, method: str):
    """Helper function. Tokenizes an Icelandic sentence."""
    # We set the option to change "1sti", ... to "1", ...
    result = []
    for token in mideind_tok.tokenize(sentence,
                                      handle_kludgy_ordinals=mideind_tok.KLUDGY_ORDINALS_MODIFY):
        kind, txt, val = token
        if method == 'pass-through':
            token = _tok_pass_through(kind, txt, val)
        elif method == 'placeholders':
            token = _tok_placeholders(kind, txt, val)
        if token:
            result.append(token)
    return result


def _tok_pass_through(kind, txt, val):
    if kind == mideind_tok.TOK.WORD:
        if val:
            return val[0][0]
        return txt
    if kind == mideind_tok.TOK.PERCENT:
        return f'{val[0]} %'
    if kind == mideind_tok.TOK.S_BEGIN:
        return None
    if kind == mideind_tok.TOK.S_END:
        return None
    return txt


def _tok_placeholders(kind, txt, val):
    if kind == mideind_tok.TOK.WORD:
        if val:
            return val[0][0]
        return txt
    if kind == mideind_tok.TOK.ORDINAL:
        return "TALA"
    if kind == mideind_tok.TOK.NUMBER:
        return "NÚMER"
    if kind == mideind_tok.TOK.PUNCTUATION:
        return txt
    if kind == mideind_tok.TOK.YEAR:
        return "ÁR"
    if kind == mideind_tok.TOK.S_BEGIN:
        pass
    if kind == mideind_tok.TOK.S_END:
        pass
    if kind == mideind_tok.TOK.DATEABS:
        return "DAGSETNING"
    if kind == mideind_tok.TOK.DATEREL:
        return "DAGSETNING"
    if kind == mideind_tok.TOK.MEASUREMENT:
        return "MÆLING"
    if kind == mideind_tok.TOK.NUMWLETTER:
        return "GILDI"
    if kind == mideind_tok.TOK.DOMAIN:
        return "LÉN"
    if kind == mideind_tok.TOK.HASHTAG:
        return "HASHTAG"
    if kind == mideind_tok.TOK.TELNO:
        return "SÍMANÚMER"
    if kind == mideind_tok.TOK.PERCENT:
        return "PRÓSENTA"
    if kind == mideind_tok.TOK.URL:
        return "VEFFANG"
    if kind == mideind_tok.TOK.AMOUNT:
        return "UPPHÆÐ"
    if kind == mideind_tok.TOK.EMAIL:
        return "TÖLVUPÓSTUR"
    if kind == mideind_tok.TOK.UNKNOWN:
        return "UNKOWN"
    return "UNKOWN"


def known_tok_fraction(sentence: str, known_tokens: Sequence[str]) -> float:
    """
    Returns the fraction of known words in the (tokenized) sentence.

    Gives better results if the sentence has been normalized to only words."""
    sent_tokens = sentence.split()
    known = 0
    token_count = len(sent_tokens)
    for token in sent_tokens:
        if token in known_tokens:
            known += 1
    return known / token_count


def contains_regexp(sentence: str, regexp: re.Pattern) -> bool:
    """Returns true if the sentence contains the regexp."""
    if re.match(regexp, sentence) is None:
        return False
    return True


def remove_non_words(sentence: str) -> str:
    """Returns the (tokenized) sentence without punctuation, numbers and other symbols."""
    result = []
    tokens = sentence.split()
    for token in tokens:
        if not contains_regexp(token, REGEXP_SUB['NOT-WORDS'][0]):
            result.append(token)
    return " ".join(result)


def should_drop(line: str,  # pylint: disable=too-many-arguments
                regexps: Sequence[re.Pattern],
                known_tokens: Sequence[str],
                keep_ratio=0.5,
                normalize=True,
                keep_sent_length=1) -> Tuple[bool, float, str]:
    """
    Returns True and the line if line should be skipped, o.w. False and line.

    If normalized=True all non-words (\d\W_) are removed from the sentence.
    If the remaining sentence contains any of the regexps it is SKIPPED.
    If the remaining sentence has length less than or equal to keep_sent_length
    is it KEPT.
    If the keep_ratio is smaller or equal to the fraction of known_tokens in
    sentence it is KEPT.
    """
    normalized_line = line
    if normalize:
        # We normalize the tokens in the sentence, by only considering words
        normalized_line = remove_non_words(line)
    if not normalized_line:
        return True, 0.0, line
    for regexp in regexps:
        if contains_regexp(normalized_line, regexp):
            return True, 0.0, line
    # we want sentences which have a minimum length
    if len(normalized_line.split()) <= keep_sent_length:
        return False, 1.0, line
    fraction = known_tok_fraction(normalized_line, known_tokens)
    # We keep lines which have a high fraction
    if keep_ratio <= fraction:
        return False, fraction, line
    return True, fraction, line
