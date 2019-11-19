""" # noqa: D213
Corpus processing.

This module exposes some useful datatypes and functions to process corpora.
"""
from pathlib import Path
import os
import re
from unicodedata import normalize
from collections import Counter
from random import sample as r_sample
from typing import Tuple, List, Dict, Iterable, Union, Callable, \
    Sequence, Iterator, Optional
from subprocess import run
from enum import Enum
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from xml.etree import ElementTree as ET

import tokenizer
import nltk
from tqdm import tqdm
from translate.storage.tmx import tmxfile
# also in sacremoses: punct norm, detok and sent split
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
TMX_2_LANG: Dict[str, Lang] = {
    'EN-GB': Lang.EN,
    'IS-IS': Lang.IS
}

REGEXP_SUB: Dict[str, Tuple[re.Pattern, str]] = {
    # Taken from https://stackoverflow.com/questions/3809401/what-is-a-good-regular-expression-to-match-a-url?noredirect=1&lq=1
    'URI-OLD': (
    re.compile(r'(http(s)?:\/\/.)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)'),
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


def _sizeof_fmt(num: float, suffix: str = 'B') -> str:
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


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


def corpus_info(path: Path) -> Tuple[str, str, int]:
    """Returns the path, size and line count of a Path."""
    size = _sizeof_fmt(path.stat().st_size)
    line_count = _get_line_count(path.resolve())
    return str(path.resolve()), size, line_count


def corpus_info_formatted(path: Path) -> str:
    """Returns the formatted path, size and line count of a Path."""
    path_s, size, lines = corpus_info(path)
    return f'{path_s:<40}{size:^15}{lines:>10}'


def read(directory: Path, lang: Lang, *modifiers) -> Optional[Path]:
    """
    Returns the path to a file in dir with given language and all modifiers.

    Assumes the naming convention: modifier-modifier.lang
    :param directory: The directory to read from.
    :param lang: The Lang to read.
    :param modifiers: A sequence of modifiers to search for.
    :return: If exists, a Path pointing to the file, o.w. error.
    """
    path = Path(directory.joinpath("-".join(modifiers)).with_suffix(f".{lang.value}"))
    if path.exists():
        return path
    raise FileNotFoundError(f"{path} does not exist")


def write(directory: Path, lang: Lang, *modifiers, overwrite=True) -> Optional[Path]:
    """
    Returns the path to a file in dir with given language and all modifiers.

    Assumes the naming convention: modifier-modifier.lang
    :param directory: The directory to write to.
    :param lang: The Lang to write.
    :param modifiers: A sequence of modifiers.
    :param overwrite: If set True, will not raise error if exists.
    :return: A Path pointing to the file.
    """
    path = Path(directory.joinpath("-".join(modifiers)).with_suffix(f".{lang.value}"))
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} exists")
    return path


def list_dir(directory: Path, langs: Sequence[Lang], *modifiers, print_info=True) -> List[Path]:
    """
    Returns the paths in dir with given languages and contain all modifiers.

    Assumes the naming convention: modifier-modifier.lang
    :param directory: The directory to list.
    :param langs: The Langs to list.
    :param modifiers: A sequence of modifiers.
    :param print_info: If set True, will print_info of files.
    :return: A List[Path] pointing to the files.
    """
    results = []
    for lang in langs:
        results.extend(directory.glob(f"*.{lang.value}"))
    if modifiers:
        results = [result for result in results for modifier in modifiers if modifier in str(result)]
    results.sort()
    if print_info:
        for result in results:
            print(corpus_info_formatted(result))
    return results


def _lang(path: Path) -> Lang:
    # The first part of the suffix is '.', omit it.
    return Lang(path.suffix[1:])


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


def tei_read_file(path: Path) -> Sequence[str]:
    """ # noqa: D205
    Reads a tei file. Returns a list of sentences, newline at end.

    Adjusted code from xml_tools.py from Róbert Kjaran <robert@kjaran.com>
    """
    NS = {'a': 'http://www.tei-c.org/ns/1.0'}
    root = ET.parse(str(path)).getroot()
    sentences = []
    # We gather all the paragraphs from the body, avoiding the divs
    for paragraph_node in root.findall('.//a:body//a:p', NS):
        for sentence_node in paragraph_node.findall('.//a:s', NS):
            tokens = [(token_node.text, token_node.attrib['type'])
                      for token_node in sentence_node.findall('./*')]
            sentence: List[str] = []
            tokens_len = len(tokens)
            for i, token in enumerate(tokens):
                if token[0] is None:
                    continue
                sentence.append(token[0])
                if i != tokens_len - 1 and (tokens[i + 1][1] != 'punctuation'):
                    sentence.append(' ')
            sentences.append(''.join(sentence) + '\n')
    return sentences


def tei_read(paths: Sequence[Path], out_path: Path) -> bool:
    """Reads a sequence of Path of TEI files from RMH and writes to a single file."""
    with out_path.open('w+') as f_out:
        with ProcessPoolExecutor(max_workers=14) as executor:
            results = list(tqdm(executor.map(
                tei_read_file,
                paths,
                chunksize=100),
                total=len(paths)))
            for result in results:
                f_out.write(''.join(result))
    return True


def peek(path: Path, length: int = 10) -> Iterator[str]:
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
    langs = [_lang(path) for path in paths]
    generators = [peek(path, length) for path in paths]
    remaining = True
    while remaining:
        for index, lang in enumerate(langs):
            try:
                sentence = next(generators[index])
                yield f'{lang.value}: {sentence}'
            except StopIteration:
                return


def combine(paths: Sequence[Path], out_path: Path) -> bool:
    """# noqa: D205
    Combines a collection of Paths to a single Path.

    The output gets written over if run multiple times.
    """
    command = ['cat'] + [str(path) for path in paths]
    with out_path.open('w+') as f_out:
        run(command, stdout=f_out, check=True)

    return True


def in_parallel(path: Path,
                out_path: Path,
                threads: int,
                func: Callable,
                chunksize: int = 4000,
                **kwargs) -> bool:
    with ProcessPoolExecutor(max_workers=threads) as executor:
        with path.open() as f_in, out_path.open('w+') as f_out:
            # get the list now since executor.map will read everyting to mem.
            f_list = f_in.readlines()
            results = tqdm(executor.map(
                partial(func, **kwargs),
                f_list,
                chunksize=chunksize),
                total=len(f_list))
            for result in results:
                f_out.write(result)
    return True


def split(path: Path, out_path_1: Path, out_path_2: Path, count) -> bool:
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


def regexp(path: Path,
           out_path: Path,
           regexps: List[Tuple[re.Pattern, str]]) -> bool:
    """ # noqa: D205
    Applies a list of regular expressions and their substitions to a Path and
    writes the result to the out_path. returns True if successful.
    """
    return in_parallel(path,
                       out_path,
                       THREADS,
                       partial(sent_regexp, regexps=regexps)
                       )


def shuffle(path: Path, out_path: Path, seed_path: Path) -> bool:
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


def sample(path: Path, count: int) -> Iterable[str]:
    """Samples count many lines from a Path."""
    with path.open() as f_in:
        # Careful, we read the whole file...
        lines = f_in.readlines()
    yield from r_sample(lines, count)


def sentence_counter(path: Path) -> Counter:
    """Returns a Counter with the sentence length as key and the count as value."""
    with path.open() as f_in:
        counter: Counter = Counter()
        for line in f_in:
            sent_length = len(line.split(" "))
            counter[sent_length] += 1
    return counter


def token_counter(path: Path) -> Counter:
    """Returns a Counter with the token as key and the count as value."""
    with path.open() as f_in:
        counter: Counter = Counter()
        for line in f_in:
            counter.update(line.strip('\n').split(" "))
    return counter


def sent_lowercase_normalize(sent: str) -> str:
    """Applies unicode lowercase and normalize on a string."""
    return normalize('NFKC', sent.casefold())


def lowercase_normalize(path: Path,
                        out_path: Path) -> bool:
    """ # noqa: D205
    Applies unicode lowercase and normalize on a Path. Writes the
    result to out_path. Returns True if successful.
    """
    return in_parallel(path,
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
    # Moses for 'is'
    if method == 'moses':
        m_tok = MosesTokenizer(lang='is')
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


def tokenize(path: Path,
             out_path: Path,
             method: str = 'pass-through') -> bool:
    """ # noqa D205
    Tokenizes a Path using the specified method. Writes the output to
    out_path. Returns True if successful.
    Supported methods for IS (only):
        IS(default): "pass-through", basic tokenization.
        IS: "placeholders", uses placeholders for some NEs.
    """
    tok = _get_tokenizer(_lang(path), method)
    return in_parallel(path,
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


def sent_token_known(sentence: str, known_tokens: Sequence[str]) -> float:
    """ # noqa: D205
    Returns the fraction of known words in the (tokenized) sentence.

    Gives better results if the sentence has been normalized to only words."""
    sent_tokens = sentence.split()
    known = 0
    token_count = len(sent_tokens)
    for token in sent_tokens:
        if token in known_tokens:
            known += 1
    return known / token_count


def sent_contains_regexp(sentence: str, regexp: re.Pattern) -> bool:
    """Returns true if the sentence contains the regexp."""
    if re.match(regexp, sentence) is None:
        return False
    return True


def sent_as_words(sentence: str) -> str:
    """Returns the (tokenized) sentence without punctuation, numbers and other symbols."""
    result = []
    tokens = sentence.split()
    for token in tokens:
        if not sent_contains_regexp(token, REGEXP_SUB['NOT-WORDS'][0]):
            result.append(token)
    return " ".join(result)


def get_skip_lines(path: Path,  # pylint: disable=too-many-arguments,too-many-locals
                   regexps: Sequence[re.Pattern],
                   known_tokens: Sequence[str],
                   keep_ratio=0.5,
                   normalize=True,
                   keep_sent_length=1) -> List[Tuple[int, float, str]]:
    """ # noqa: D205
    Returns a list of line number and lines which should be skipped.

    If normalized=True all non-words (\d\W_) are removed from the sentence.
    If the remaining sentence contains any of the regexps it is SKIPPED.
    If the remaining sentence has length less than or equal to keep_sent_length
    is it KEPT.
    If the keep_ratio is smaller or equal to the fraction of known_tokens in
    sentence it is KEPT.
    """
    skip_lines: List[Tuple[int, float, str]] = []
    with ProcessPoolExecutor(max_workers=THREADS) as executor:
        with path.open() as f_in:
            f_list = f_in.readlines()
            results = tqdm(executor.map(
                partial(sent_skip_line,
                        regexps=regexps,
                        known_tokens=known_tokens,
                        keep_ratio=keep_ratio,
                        normalize=normalize,
                        keep_sent_length=keep_sent_length),
                f_list,
                chunksize=CHUNKSIZE),
                total=len(f_list))
            for index, result in enumerate(results):
                skip, fraction, line = result
                if skip:
                    skip_lines.append((index + 1, fraction, line))
    return skip_lines


def sent_skip_line(line: str,  # pylint: disable=too-many-arguments
                   regexps: Sequence[re.Pattern],
                   known_tokens: Sequence[str],
                   keep_ratio=0.5,
                   normalize=True,
                   keep_sent_length=1) -> Tuple[bool, float, str]:
    """ # noqa: D205
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
        normalized_line = sent_as_words(line)
    if not normalized_line:
        return True, 0.0, line
    for regexp in regexps:
        if sent_contains_regexp(normalized_line, regexp):
            return True, 0.0, line
    # we want sentences which have a minimum length
    if len(normalized_line.split()) <= keep_sent_length:
        return False, 1.0, line
    fraction = sent_token_known(normalized_line, known_tokens)
    # We keep lines which have a high fraction
    if keep_ratio <= fraction:
        return False, fraction, line
    return True, fraction, line


def skip_lines(path: Path, out_path, lines_in: List[int]) -> bool:
    """Writes the path to out_path, skipping the lines given."""
    lines = list(lines_in)
    with path.open() as f_in, out_path.open('w+') as f_out:
        next_skip = -1
        if lines:
            next_skip = lines.pop(0)
        for index, line in enumerate(f_in):
            if index + 1 == next_skip:
                if lines:
                    next_skip = lines.pop(0)
            else:
                f_out.write(line)
    return True


def sent_process_v1(sent: str, lang: Lang) -> str:
    """ # noqa: D205
    Applies the same preprocessing steps to a sentence as used in
    baseline Moses en-is/is-en MT system.

    1. Lowercase & unicode normalize NFKC.
    2. Add URI placeholders.
    3. Tokenize "is" with "pass-through", "en" with "toktok".
    4. Fix URI placeholders and add more placeholders []()<>.
    """
    sent = sent_lowercase_normalize(sent)
    regexps = [
        REGEXP_SUB['URI'],
        REGEXP_SUB['EMPTY-BRACKETS']
    ]
    sent = sent_regexp(sent, regexps)
    if lang == Lang.EN:
        sent = sent_tokenize(sent, lang, method="toktok")
    else:
        sent = sent_tokenize(sent, lang, method="pass-through")
    regexps = [
        REGEXP_SUB['PIPE'],
        REGEXP_SUB['FIX-URI'],
        REGEXP_SUB['LT'],
        REGEXP_SUB['GT'],
        REGEXP_SUB['BRACKET-OPEN'],
        REGEXP_SUB['BRACKET-CLOSE']
    ]
    sent = sent_regexp(sent, regexps)

    return sent
