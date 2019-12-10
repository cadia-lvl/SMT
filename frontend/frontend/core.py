"""
Sentence level processing. Some useful functions to process sentences.
"""
import re
from collections import Counter
from unicodedata import normalize
from typing import Tuple, List, Dict, Callable, \
    Sequence, Union
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
        '_uri_'),
    'IS-COMBINE-NEWLINE': (re.compile(r'([\w]+)\.\n([a-záðéíóúýþæö])'),
                           r'\1. \2'),
    'IS-SPLIT-NEWLINE': (re.compile(r'([\w\(\)\[\]\.]{2,})\.([A-ZÁÐÉÍÓÚÝÞÆÖ])'),
                         r'\1. \2'),
    'URI': (re.compile(
        r"((http(s)?:\/\/)|(www)|([-a-zA-Z0-9:%_\+.~#?&/=]+?@))+([-a-zA-Z0-9@:%_\+.~#?&/=]+)"),
            '_uri_'),
    'URI-SIMPLE': (re.compile(r"([-a-zA-Z0-9@:%_\+.~#?&/=]+?)(\.is|\.com)"), "_uri_"),
    'EMPTY-BRACKETS': (re.compile(r"[\[\(]\s*[\]\)]"), ""),
    # u'\u007c' - |
    'PIPE': (re.compile(r"\u007c"), '_pipe_'),
    # u'\u003c', u'\u003e' - <, >
    'LT': (re.compile(r"\u003c"), '_lt_'),
    'GT': (re.compile(r"\u003e"), '_gt_'),
    # u'\u005b', u'\u005d' - [, ]
    'BRACKET-OPEN': (re.compile(r"\u005b"), '_brac_open_'),
    'BRACKET-CLOSE': (re.compile(r"\u005d"), '_brac_close_'),
    'FIX-URI': (re.compile(r"_ uri _"), '_uri_'),
    'CRYLLIC': (re.compile(r'.*[\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F]+.*'),
                ''),
    'GREEK': (re.compile(r'.*[\u0370-\u03bb\u03bd-\u03FF\u1F00-\u1FFF]+.*'), ''),
    'UNKNOWN-CHARS': (re.compile(r'.*[žčšè¿ğūįł]+.*'), ''),
    'NOT-WORDS': (re.compile(r'.*[\W\d_].*'), ''),
    'NOT-WORDS-OLD': (re.compile(r'.*[\d();.:,•\-=?!_+@].*'), '')
}


def regexp(sent: str, regexps: List[Tuple[re.Pattern, str]], count=False) -> Union[str, Tuple[str, Counter]]:
    """Applies a list of regular expressions and their substitutions to a string.

    :param sent: The sentence to process.\n
    :param regexps: A list of Tuples (re.Pattern, str).\n
    The pattern is used to match and the str is used as a replacement.
    The str supports referencing groups in the match expression.\n
    :param count: If set True, will count instances of replacements of each expression.
    :return: The processed sentence and a Counter which contains the number of substitutions made for each Pattern.
    """
    processed_line = sent
    if count:
        replacements = Counter()
    for regular_expression, sub_string in regexps:
        processed_line, num_replacements = re.subn(
            regular_expression, sub_string, processed_line)
        if count:
            replacements[str(regular_expression)] += num_replacements
    if count:
        return processed_line, replacements
    return processed_line


def lowercase_normalize(sent: str) -> str:
    """Applies unicode lowercase and normalize (NFKC) on a string.

    :param sent: The sentence to process.\n
    :return: The processed sentence.
    """
    return normalize('NFKC', sent.casefold())


def get_tokenizer(lang: Lang, method: str) -> Callable[[str], List[str]]:
    """Returns a tokenizer for a specified method and additional arguments.

    Supported methods:

    - IS(default) "shallow": Basic tokenization, no abbreviation expansion.
    - IS: "pass-through": Mideind deep tokenization with extra handling of percentages (50 %).
    - IS: "placeholders", uses placeholders for some NEs.
    - IS: "moses", uses Moses tokenization. Poor performance for IS.
    - EN(default): "moses", Moses tokenization, splits up URLs. Poor abbreviation handling.
    - EN: "nltk", splits up URLs.
    - EN: "toktok", handles URLs, does not handle "." but at the end.
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
    if lang == Lang.IS:
        if method == 'moses':
            m_tok = MosesTokenizer(lang='is')
            return partial(m_tok.tokenize, escape=False)
        if not method:
            return partial(_tokenize_is, method="shallow")
        return partial(_tokenize_is, method=method)


def apply_tokenizer(sentence: str, tokenizer: Callable[[str], List[str]]) -> str:
    """Applies a tokenization function to a sentence.

    :param sentence: The sentence to process.\n
    :param tokenizer: The tokenizer function to use.\n
    :return: The processed sentence.
    """
    return " ".join(tokenizer(sentence))


def tokenize(sentence: str, lang: Lang, method: str):
    """Tokenizes a sentence using the specified method. See get_tokenizer() for supported methods.

    :param sentence: The sentence to process.\n
    :param lang: The language of the sentence.\n
    :param method: The tokenization method to use. See get_tokenizer() for supported methods.\n
    :return: The processed sentence.

    """
    tok = get_tokenizer(lang, method)
    return apply_tokenizer(sentence, tok)


def _tokenize_is(sentence: str, method: str):
    """Helper function. Tokenizes an Icelandic sentence."""
    result = []
    if method == "shallow":
        for sent in mideind_tok.split_into_sentences(sentence):
            result.extend(sent.split(" "))
    else:
        # We set the option to change "1sti", ... to "1", ...
        for token in mideind_tok.tokenize(sentence,
                                          handle_kludgy_ordinals=mideind_tok.KLUDGY_ORDINALS_MODIFY):
            kind, txt, val = token
            if method == 'pass-through':
                token = _tok_pass_through(kind, txt, val)
            elif method == 'placeholders':
                token = _tok_placeholders(kind, txt, val)
            else:
                raise ValueError(f"Unkown tokenization method={method}")
            if token:
                result.append(token)
    return result


def _tok_pass_through(kind, txt, val):
    if kind == mideind_tok.TOK.WORD:
        if val:
            return val[0][0]
        return txt
    if kind == mideind_tok.TOK.PERCENT:
        return f'{val[0]:g} %'
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
    """Returns the fraction of known words in the sentence. Works best if the sentence has been tokenized and
    if the sentence has been normalized to only words.

    :param sentence: The sentence to processes.\n
    :param known_tokens: A Sequence of known tokens to compare to.\n
    :return: The fraction of known tokens in sentence according to "known_tokens".
    """
    sent_tokens = sentence.split()
    known = 0
    token_count = len(sent_tokens)
    for token in sent_tokens:
        if token in known_tokens:
            known += 1
    return known / token_count


def contains_regexp(sentence: str, regexp: re.Pattern) -> bool:
    """Checks if the sentence contains the regexp.

    :param sentence: The sentence to process.
    :param regexp: The regular expression to search for.
    :return: True if the regular expression is found in the sentence.
    """
    if re.match(regexp, sentence) is None:
        return False
    return True


def remove_non_words(sentence: str) -> str:
    """Normalizes a sentence by removing all words which contain punctuation, numbers and other non-word symbols.

    :param sentence: The sentence to process.\n
    :return: The processed sentence.
    """
    result = []
    tokens = sentence.split()
    for token in tokens:
        if not contains_regexp(token, REGEXP_SUB['NOT-WORDS'][0]):
            result.append(token)
    return " ".join(result)


def should_drop(line: str,
                regexps: Sequence[re.Pattern],
                known_tokens: Sequence[str],
                keep_ratio=0.5,
                normalize=True,
                keep_sent_length=1) -> Tuple[bool, float, str]:
    """Decides if a line should be dropped given the criteria.
    Regexp defines a black-list of regular expressions.

    If normalized=True all non-words are removed from the sentence before counting the numer of words.\n
    If the remaining sentence contains any of the regexps it is DROPPED.\n
    If the remaining sentence has length less than or equal to keep_sent_length is it KEPT.\n
    If the keep_ratio is smaller or equal to the fraction of known_tokens in sentence it is KEPT.

    :param line: The sentence to process.\n
    :param regexps: A black-list of regular expressions. If any is matched in a sentence, it is DROPPED.\n
    :param known_tokens: A whitelist of tokens which are considered as known.\n
    :param keep_ratio: If the fraction of known tokens is higher than keep_ration, the sentence is KEPT.\n
    :param normalize: If True, we first normalize the sentence by removing all words which contain non-words.\n
    :param keep_sent_length: If a sentence contains keep_sent_length of fewer words, it is KEPT.\n
    :return: A Tuple (Should drop, the known fraction, the line).\n
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
