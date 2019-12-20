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
# also in sacremoses: punct norm, detok and sent split
from sacremoses import MosesTokenizer, MosesDetokenizer

from . import definitions as d


class Lang(Enum):
    """An enum for supported ISO 639-1 language codes. String based"""
    EN = 'en'
    IS = 'is'


def regexp(sent: str, regexps: List[Dict], count=False) -> Union[str, Tuple[str, Counter]]:
    """Applies a list of regular expressions and their substitutions to a string.

    :param sent: The sentence to process.\n
    :param regexps: A list of Dict with keywords for the subn expression.\n
    Must contain "pattern" and "replace", the "string" is supplied by the function.\n
    :param count: If set True, will count instances of replacements of each expression.
    :return: The processed sentence and a Counter which contains the number of substitutions made for each Pattern.
    """
    processed_line = sent
    if count:
        replacements = Counter()
    for keywords in regexps:
        processed_line, num_replacements = re.subn(string=processed_line, **keywords)
        if count:
            replacements[str(keywords['pattern'])] += num_replacements
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
    """
    if lang == Lang.EN:
        # o.w. we use Moses
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


def detokenize(sentence: str, lang: Lang, method: str):
    """Detokenizes a sentence using the specified method.

    :param sentence: The sentence to process.\n
    :param lang: The language of the sentence.\n
    :param method: The detokenization method to use.\n
    :return: The processed sentence.

    Supported methods:

    - IS(default) "shallow": Will tokenize the input and then detokenize it again. Mideind tokenizer expects the
    input to be a List[TOK], not a string.
    - EN(default): "moses": The input needs to be preprocessed by "pre_detokenization_moses()" before detokenization.

    """
    if lang == Lang.EN and method == "moses":
        tokens = sentence.split(" ")
        detok = MosesDetokenizer(lang='en')
        return detok.detokenize(tokens, unescape=False)
    if lang == Lang.IS and method == 'shallow':
        tokenized = list(mideind_tok.tokenize(sentence, normalize=False))
        return mideind_tok.detokenize(tokenized, normalize=False)
    raise ValueError("Unkown method for detokenization")


def pre_detokenization_moses(sentence: str) -> str:
    """
    Fixes the translated
    """
    return re.sub(r"' ", r"'", sentence)


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
        if not contains_regexp(token, d.NOT_WORDS):
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
