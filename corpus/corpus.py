""" # noqa: D213
Corpus processing.

This module exposes some useful datatypes and functions to process corpora.
"""
from pathlib import Path

import os
import re
from unicodedata import normalize
from collections import Counter
from random import sample
from typing import Tuple, List, Dict, Iterable, Union, Callable, Iterator
from subprocess import run
from enum import Enum
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import tokenizer
import nltk
from translate.storage.tmx import tmxfile
# also: punct norm, detok and sent split
from sacremoses import MosesTokenizer
nltk.download('punkt')

# Some parts of the processing support threading, set the value here.
THREADS = int(os.environ.get('THREADS', 4))
CHUNKSIZE = 4000


class Lang(Enum):
    """An enum for supported ISO 639-1 language codes. String based"""  # noqa: D203
    EN = 'en'
    IS = 'is'


# A dict to map between "ISO 639-1-ISO 3166-1" to ISO 639-1 (two letter language code)
TMX_2_LANG = {
    'EN-GB': Lang.EN,
    'IS-IS': Lang.IS
}


def corpus_lang(path: Path) -> Lang:
    # The first part of the suffix is '.', omit it.
    return Lang(path.suffix[1:])


def _sizeof_fmt(num: float, suffix: str = 'B') -> str:
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def corpus_info(path: Path) -> Tuple[str, str, int]:
    """Returns the path, size and line count of a Path."""
    size = _sizeof_fmt(path.stat().st_size)
    line_count = _get_line_count(path.resolve())
    return (str(path.resolve()), size, line_count)


def corpus_info_formatted(path: Path) -> str:
    """Returns the formatted path, size and line count of a Path."""
    path_s, size, lines = corpus_info(path)
    return f'{path_s:<40}{size:^15}{lines:>10}'


def corpus_create_path(path: Path, new_name: str) -> Path:
    """Creates a new Path in same dir as path. Keeps the same language."""
    return path.with_name(f'{new_name}.{corpus_lang(path).value}')


def corpora_create_path(paths: List[Path], new_name: str) -> Path:
    """Creates a new Path in same dir as first path. Keeps the same language."""
    for path in paths:
        return corpus_create_path(path, new_name)
    raise ValueError("No paths given.")


def pipeline_load(data_dir: Path,
                  stages: List[str],
                  lang: Lang = Lang.IS) \
        -> Dict[str, Union[Path, None]]:
    """Loads the processed pipeline as a dict from a directory given stages."""
    pipeline: Dict[str, Union[Path, None]] = dict()
    for stage in stages:
        files = list(data_dir.glob(f'{stage}.{lang.value}'))
        if len(files) == 1:
            pipeline[stage] = files[0]
        else:
            pipeline[stage] = None
    return pipeline


def _get_line_count(path: Path) -> int:
    """Count the number of new-lines in a file."""
    with path.open('rb') as f_in:
        lines = 0
        buf_size = 1024 * 1024
        read_f = f_in.raw.read  # type: ignore

        buf = read_f(buf_size)
        while buf:
            lines += buf.count(b'\n')
            buf = read_f(buf_size)

    return lines


def tmx_split(paths: Tuple[Path],
              src_lang: str,
              tar_lang: str) -> List[Tuple[Path, Path]]:
    """Split a tmx file to ParaCorpus."""
    result: List[Tuple[Path, Path]] = list()
    for tmx_path in paths:
        # We read the file as bytes since the xml defines an encoding.
        with tmx_path.open('rb') as f_in:
            tmx = tmxfile(f_in, src_lang, tar_lang)
        # We assume that there is only one stem
        src_path = tmx_path.with_name(
            f'{tmx_path.stem}.{TMX_2_LANG[src_lang].value}')
        tar_path = tmx_path.with_name(
            f'{tmx_path.stem}.{TMX_2_LANG[tar_lang].value}')
        with src_path.open('w+') as f_src, tar_path.open('w+') as f_tar:
            for node in tmx.unit_iter():
                f_src.write(node.source + '\n')
                f_tar.write(node.target + '\n')
        result.append((src_path, tar_path))
    return result


def corpus_peek(path: Path, length: int = 10) -> Iterator[str]:
    """Returns the first length many lines from a given path."""
    with path.open() as f:
        index = 0
        for line in f:
            index += 1
            yield line
            if index == length:
                return


def corpora_peek(paths: List[Path], length: int = 10) -> Iterator[str]:
    """ # noqa: D205
    Returns a generator of formatted strings of the first length lines of corpora."""
    langs = [corpus_lang(path) for path in paths]
    generators = [corpus_peek(path, length) for path in paths]
    remaining = True
    while remaining:
        for index, lang in enumerate(langs):
            try:
                sentence = next(generators[index])
                yield f'{lang.value}: {sentence}'
            except StopIteration:
                return


def corpora_combine(paths: Tuple[Path], out_path: Path) -> bool:
    """# noqa: D205
    Combines a collection of Paths to a single Path.

    The output gets written over if run multiple times.
    """
    command = ['cat'] + [str(path) for path in paths]
    with out_path.open('w+') as f_out:
        run(command, stdout=f_out, check=True)

    return True


def parallel_process(path: Path,
                     out_path: Path,
                     threads: int,
                     func: Callable,
                     chunksize: int = 4000,
                     **kwargs) -> bool:
    with ProcessPoolExecutor(max_workers=threads) as executor:
        with path.open() as f_in, out_path.open('w+') as f_out:
            results = executor.map(
                partial(func, **kwargs),
                f_in,
                chunksize=chunksize)
            for result in results:
                f_out.write(result)
    return True


def corpus_split(path: Path, out_path_1: Path, out_path_2: Path, count) -> bool:
    """ # noqa: D205
    Splits a Path to two Path with stages. The latter stage has count
    many lines
    """
    with path.open() as f_in:
        # Careful, we read all the lines
        lines = f_in.readlines()
        with out_path_1.open('w+') as f_s1, \
                out_path_2.open('w+') as f_s2:
            f_s1.writelines(lines[:-count])
            f_s2.writelines(lines[-count:])

    return True


def sent_regexp(sent: str, regexps: List[Tuple[re.Pattern, str]]) -> str:
    """ # noqa: D205
    Applies a list of regular expressions and their substitions to a string.
    """
    processed_line = sent
    for regular_expression, sub_string in regexps:
        processed_line = re.sub(
            regular_expression, sub_string, processed_line)
    return processed_line


def corpus_regexp(path: Path,
                  out_path: Path,
                  regexps: List[Tuple[re.Pattern, str]]) -> bool:
    """ # noqa: D205
    Applies a list of regular expressions and their substitions to a Path and
    writes the result to the out_path. returns True if successful.
    """
    return parallel_process(path,
                            out_path,
                            THREADS,
                            partial(sent_regexp, regexps=regexps)
                            )


def corpus_shuffle(path: Path, out_path: Path, seed_path: Path) -> bool:
    """ # noqa: D205
    Shuffles a Path using the seed_path as a random seed. Writes the result
    to out_path. Returns True if successful.
    """
    command = [
        'shuf',
        f'--random-source={str(seed_path)}',
        f'{str(path)}'
    ]
    with out_path.open('w+') as f_out:
        run(command, stdout=f_out, check=True)
    return True


def corpus_sample(path: Path, count: int) -> Iterable[str]:
    """Samples count many lines from a Path."""
    with path.open() as f_in:
        # Careful, we read the whole file...
        lines = f_in.readlines()
    yield from sample(lines, count)


def corpus_sentence_counter(path: Path) -> Counter:
    """Returns a Counter with the sentence length as key and the count as value."""
    with path.open() as f_in:
        counter: Counter = Counter()
        for line in f_in:
            sent_length = len(line.split(" "))
            counter[sent_length] += 1
    return counter


def corpus_token_counter(path: Path) -> Counter:
    """Returns a Counter with the token as key and the count as value."""
    with path.open() as f_in:
        counter: Counter = Counter()
        for line in f_in:
            counter.update(line.strip('\n').split(" "))
    return counter


def sent_lowercase_normalize(sent: str) -> str:
    """Applies unicode lowercase and normalize on a string."""
    return normalize('NFKC', sent.casefold())


def corpus_lowercase_normalize(path: Path,
                               out_path: Path) -> bool:
    """ # noqa: D205
    Applies unicode lowercase and normalize on a Path. Writes the
    result to out_path. Returns True if successful.
    """
    return parallel_process(path,
                            out_path,
                            THREADS,
                            sent_lowercase_normalize)


def _get_tokenizer(lang: Lang, method: str) -> Callable[[str], List[str]]:
    """ # noqa D205
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
    return partial(sent_is_tokenize, method=method)


def sent_tokenizer(sentence: str, tokenizer: Callable[[str], List[str]]) -> str:
    """Applies a tokenization function to a sentence."""
    return " ".join(tokenizer(sentence)) + "\n"


def sent_tokenize(sentence: str, lang: Lang, method: str = 'pass-through'):
    """ # noqa D205
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
    tok = _get_tokenizer(lang, method)
    return sent_tokenizer(sentence, tok)


def corpus_tokenize(path: Path,
                    out_path: Path,
                    method: str = 'pass-through') -> bool:
    """ # noqa D205
    Tokenizes a Path using the specified method. Writes the output to
    out_path. Returns True if successful.
    Supported methods for IS (only):
        IS(default): "pass-through", basic tokenization.
        IS: "placeholders", uses placeholders for some NEs.
    """
    tok = _get_tokenizer(corpus_lang(path), method)
    return parallel_process(path,
                            out_path,
                            THREADS,
                            partial(sent_tokenizer, tokenizer=tok)
                            )


def sent_is_tokenize(sentence: str, method: str):
    """Helper function. Tokenizes an Icelandic sentence."""
    # We set the option to change "1sti", ... to "1", ...
    result = []
    for token in tokenizer.tokenize(sentence,
                                    handle_kludgy_ordinals=tokenizer.KLUDGY_ORDINALS_MODIFY):
        kind, txt, val = token
        if method == 'pass-through':
            token = _tok_pass_through(kind, txt, val)
        elif method == 'placeholders':
            token = _tok_placeholders(kind, txt, val)
        if token:
            result.append(token)
    return result


def _tok_pass_through(kind, txt, val):
    if kind == tokenizer.TOK.WORD:
        if val:
            return val[0][0]
        return txt
    if kind == tokenizer.TOK.PERCENT:
        return f'{val[0]} %'
    if kind == tokenizer.TOK.S_BEGIN:
        return None
    if kind == tokenizer.TOK.S_END:
        return None
    return txt


def _tok_placeholders(kind, txt, val):
    if kind == tokenizer.TOK.WORD:
        if val:
            return val[0][0]
        return txt
    if kind == tokenizer.TOK.ORDINAL:
        return "TALA"
    if kind == tokenizer.TOK.NUMBER:
        return "NÚMER"
    if kind == tokenizer.TOK.PUNCTUATION:
        return txt
    if kind == tokenizer.TOK.YEAR:
        return "ÁR"
    if kind == tokenizer.TOK.S_BEGIN:
        pass
    if kind == tokenizer.TOK.S_END:
        pass
    if kind == tokenizer.TOK.DATEABS:
        return "DAGSETNING"
    if kind == tokenizer.TOK.DATEREL:
        return "DAGSETNING"
    if kind == tokenizer.TOK.MEASUREMENT:
        return "MÆLING"
    if kind == tokenizer.TOK.NUMWLETTER:
        return "GILDI"
    if kind == tokenizer.TOK.DOMAIN:
        return "LÉN"
    if kind == tokenizer.TOK.HASHTAG:
        return "HASHTAG"
    if kind == tokenizer.TOK.TELNO:
        return "SÍMANÚMER"
    if kind == tokenizer.TOK.PERCENT:
        return "PRÓSENTA"
    if kind == tokenizer.TOK.URL:
        return "VEFFANG"
    if kind == tokenizer.TOK.AMOUNT:
        return "UPPHÆÐ"
    if kind == tokenizer.TOK.EMAIL:
        return "TÖLVUPÓSTUR"
    if kind == tokenizer.TOK.UNKNOWN:
        return "UNKOWN"
    return "UNKOWN"


def sent_process_v1(sent: str, lang: Lang) -> str:
    """ # noqa: D205
    Applies the same preprocessing steps to a sentence as used in
    baseline Moses en-is/is-en MT system.

    1. Lowercase & unicode normalize NFKC.
    2. Tokenize "is" with "pass-through", "en" with "toktok".
    3. Add URI placeholders for URIs and []()<>.
    """
    sent = sent_lowercase_normalize(sent)
    if lang == Lang.EN:
        sent = sent_tokenize(sent, lang, method="toktok")
    else:
        sent = sent_tokenize(sent, lang, method="pass-through")
    # u'\u007c' - |
    pipe_reg = re.compile(r"\u007c")
    # u'\u003c', u'\u003e' - <, >
    lt_reg = re.compile(r"\u003c")
    gt_reg = re.compile(r"\u003e")

    # u'\u005b', u'\u005d' - [, ]
    bracket_open_reg = re.compile(r"\u005b")
    bracket_close_reg = re.compile(r"\u005d")

    # Taken from https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url?noredirect=1&lq=1
    uri_reg = re.compile(
        r"(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)")
    empty_bracets = re.compile(r"[\[\(]\s*[\]\)]")
    regexps = [
        (uri_reg, '@uri@'),
        (empty_bracets, ""),
        (pipe_reg, '@pipe@'),
        (lt_reg, '@lt@'),
        (gt_reg, '@gt@'),
        (bracket_open_reg, '@brac_open@'),
        (bracket_close_reg, '@brac_close@')
    ]
    sent = sent_regexp(sent, regexps)
    return sent
