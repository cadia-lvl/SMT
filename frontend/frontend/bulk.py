"""A collection of functions to process files, a sentence per line. Uses multiple threads to process.

- Uses pathlib.Path to manipulate files.
- Has a naming convention to read and write files: modifier1-modifier2.lang. Use the "read()" and "write()" functions
to avoid implementation details.
"""
import re
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from pathlib import Path
from random import sample as r_sample
from subprocess import run
from typing import Dict, Tuple, Optional, Sequence, List, Iterator, Callable, Iterable
import os
from xml.etree import ElementTree as ET

from tqdm import tqdm
from translate.storage.tmx import tmxfile

from .core import Lang, get_tokenizer, apply_tokenizer, should_drop
from .core import regexp as c_regexp, lowercase_normalize as c_lower_norm

TMX_2_LANG: Dict[str, Lang] = {
    'EN-GB': Lang.EN,
    'IS-IS': Lang.IS
}
"""A dict to map between "ISO 639-1-ISO 3166-1" to ISO 639-1 (two letter language code).
Used for .tmx file reading.
"""

# Some parts of the processing support threading, set the value here.
THREADS = int(os.environ.get('THREADS', 4))
"""Some parts of the processing support threading.
Set the number of threads using core.THREADS = 4.

Default value is 4.
"""
CHUNKSIZE = 4000
"""The chunksize/number of sentences sent to each thread during parallel processing.
Set the chunksize using core.CHUNKSIZE = 4000. A higher values are often better.

Default value is 4000.
"""


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


def info(path: Path) -> Tuple[str, str, int]:
    """Get some basic information of the file input.

    :param path: The pathlib.Path to the file.\n
    :return: A tuple (path, size, line count) of the input.
    """
    size = _sizeof_fmt(path.stat().st_size)
    line_count = _get_line_count(path.resolve())
    return str(path.resolve()), size, line_count


def info_formatted(path: Path) -> str:
    """Get some basic information of the file input and returns as a formatted string.

    :param path: The pathlib.Path to the file.\n
    :return: Returns the formatted bulk.info()
    """
    path_s, size, lines = info(path)
    return f'{path_s:<40}{size:^15}{lines:>10}'


def read(directory: Path, lang: Lang, *modifiers) -> Optional[Path]:
    """A handy helper function to retrieve the pathlib.Path given a collection of modifiers.
    Works as a nice abstraction from the implementation of the naming convention.

    Assumes the naming convention: modifier-modifier.lang\n
    :param directory: The directory to search for the modifiers.\n
    :param lang: The core.Lang of the file to read.\n
    :param modifiers: A sequence of modifiers to search for.\n
    :return: If exists, returns a Path pointing to the file, o.w. error.
    """
    path = Path(directory.joinpath("-".join(modifiers)).with_suffix(f".{lang.value}"))
    if path.exists():
        return path
    raise FileNotFoundError(f"{path} does not exist")


def write(directory: Path, lang: Lang, *modifiers, overwrite=True) -> Optional[Path]:
    """A handy helper function to create a pathlib.Path given a collection of modifiers.
    Works as a nice abstraction from the implementation of the naming convention.

    Assumes the naming convention: modifier-modifier.lang\n
    :param directory: The directory to write to.\n
    :param lang: The Lang to write.\n
    :param modifiers: A sequence of modifiers.\n
    :param overwrite: If set True, will not raise error if the file exists.\n
    :return: A pathlin.Path pointing to the file.
    """
    path = Path(directory.joinpath("-".join(modifiers)).with_suffix(f".{lang.value}"))
    if path.exists() and not overwrite:
        raise FileExistsError(f"{path} exists")
    return path


def list_dir(directory: Path, langs: Sequence[Lang], *modifiers, print_info=True) -> List[Path]:
    """A handy helper function to list a pathlib.Path given a collection of modifiers.
    Works as a nice abstraction from the implementation of the naming convention.

    Assumes the naming convention: modifier-modifier.lang\n
    :param directory: The directory to list.\n
    :param langs: The core.Langs to list.\n
    :param modifiers: A sequence of modifiers.\n
    :param print_info: If set True, will print_info of files.\n
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
            print(info_formatted(result))
    return results


def _lang(path: Path) -> Lang:
    # The first part of the suffix is '.', omit it.
    return Lang(path.suffix[1:])


def tmx_split(paths: Tuple[Path],
              src_lang: str,
              tar_lang: str) -> List[Tuple[Path, Path]]:
    """Split a collection tmx file to multiple language files with a line per sentence.

    :param paths: A sequence of tmx files to split.\n
    :param src_lang: The source language code as defined in the .tmx file.\n
    :param tar_lang: The target language code as defined in the .tmx file.\n
    :return: A List of Tuples with pathlib.Path pointing to the source and target language files.
    """
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
    """Reads a tei file to extract the contents. Hand-tailored to reading the RMH.

    Adjusted code from xml_tools.py from Róbert Kjaran <robert@kjaran.com>

    :param path: A pathlib.Path to the .tei file to read.\n
    :return: A List of sentences as defined in the .tei file.
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
    """Reads a sequence of Path of TEI files from RMH and writes to a single file.
    Uses multiple threads.

    :param paths: A Sequence of pathlib.Path of .tei files to read.\n
    :param out_path: pathlib.Path to write the contents to.\n
    :return: True if successful.
    """
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
    """A handy function to yield the first lines of a file.

    :param path: The pathlib.Path of the file to peek into.\n
    :param length: The number of lines to yield.\n
    :return: An iterator yielding the next line.
    """
    with path.open() as f:
        index = 0
        for line in f:
            index += 1
            yield line
            if index == length:
                return


def peeks(paths: List[Path], length: int = 10) -> Iterator[str]:
    """A handy function to yield the first lines of multiple files.
    Formats the output.

    :param paths: A list of pathlib.Path of the files to peek into.\n
    :param length: The number of lines to yield from each file.\n
    :return: An iterator yielding the next line from multiple files at once, prepended with the language of the file.
    """
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
    """Combines a collection of files to a single file.
    The output gets written over if run multiple times.

    :param paths: A Sequence of pathlib.Path to concatenate together.\n
    :param out_path: A pathlib.Path to write the result to.\n
    :return: True if successful.
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
    """Runs the given function with **kwargs arguments in parallel on the given file.

    :param path: The pathlib.Path of the file to process.\n
    :param out_path: A pathlib.Path to write the result to.\n
    :param threads: The number of threads to use.\n
    :param func: The function to apply per line.\n
    :param chunksize: The number of lines to process in parallel.\n
    :param kwargs: The arguments to the function to apply.\n
    :return: True if successful.
    """
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
    """Splits a file to the two files provided. The latter file will have count number of lines.

    :param path: The pathlib.Path of the file to split.\n
    :param out_path_1: A pathlib.Path to write the first x lines to.\n
    :param out_path_2: A pathlib.Path to write count last lines to.\n
    :param count: The number of lines the latter file should have.\n
    :return: True if succesful.
    """
    with path.open() as f_in:
        # Careful, we read all the lines
        lines = f_in.readlines()
        with out_path_1.open('w+') as f_s1, \
                out_path_2.open('w+') as f_s2:
            f_s1.writelines(lines[:-count])
            f_s2.writelines(lines[-count:])

    return True


def regexp(path: Path,
           out_path: Path,
           regexps: List[Tuple[re.Pattern, str]]) -> bool:
    """Applies a list of regular expressions and their substitions to each line in a file.
    Uses multiple threads.

    :param path: The pathlib.Path of the file to apply the regular expression to.\n
    :param out_path: A pathlib.Path to write the result to.\n
    :param regexps: A list of Tuples (re.Pattern, str).
    The pattern is used to match and the str is used as a replacement.
    The str supports referencing groups in the match expression.\n
    :return: True if successful.
    """
    return in_parallel(path,
                       out_path,
                       THREADS,
                       partial(c_regexp, regexps=regexps)
                       )


def shuffle(path: Path, out_path: Path, seed_path: Path) -> bool:
    """Shuffles a file using a file as a random seed.

    :param path: The pathlib.Path of the file to shuffle.\n
    :param out_path: A pathlib.Path to write the result to.\n
    :param seed_path: The pathlib.Path to use a as a random seed. Can be the input file.\n
    :return: True if successful.
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
    """Yields a random sample of count many lines from a file.

    :param path: The pathlib.Path of the file to sample from.\n
    :param count: The number of lines to sample.\n
    :return: An iterator of strings.
    """
    with path.open() as f_in:
        # Careful, we read the whole file...
        lines = f_in.readlines()
    yield from r_sample(lines, count)


def sentence_counter(path: Path) -> Counter:
    """Count the number of sentences in a file.

    :param path: The pathlib.Path of the file to count.\n
    :return: A collections.Counter with the sentence length as key and the count as value.
    """
    with path.open() as f_in:
        counter: Counter = Counter()
        for line in f_in:
            sent_length = len(line.split(" "))
            counter[sent_length] += 1
    return counter


def token_counter(path: Path) -> Counter:
    """Count the number of unique tokens in a file.
    A collections.Counter with the token as key and the count as value.

    :param path: The pathlib.Path of the file to count.\n
    :return: A collections.Counter with the token as key and the count as value.
    """
    with path.open() as f_in:
        counter: Counter = Counter()
        for line in f_in:
            counter.update(line.strip('\n').split(" "))
    return counter


def lowercase_normalize(path: Path,
                        out_path: Path) -> bool:
    """Applies unicode lowercase and normalize on a file.
    Uses many threads.

    :param path: The pathlib.Path of the file to lowercase and normalize.\n
    :param out_path: A pathlib.Path to write the result to.\n
    :return: True if successful.
    """
    return in_parallel(path,
                       out_path,
                       THREADS,
                       c_lower_norm)


def tokenize(path: Path,
             out_path: Path,
             method: str = 'pass-through') -> bool:
    """Tokenizes a file using the specified method. Reads the language from the filename.
    See core.tokenize() for accepted methods. Uses many threads.

    :param path: The pathlib.Path of the file to tokenize.\n
    :param out_path: A pathlib.Path to write the result to.\n
    :param method: The tokenization method to use. See core.tokenize() for accepted methods.\n
    :return: True if successful.
    """
    tok = get_tokenizer(_lang(path), method)
    return in_parallel(path,
                       out_path,
                       THREADS,
                       partial(apply_tokenizer, tokenizer=tok, add_newline=True)
                       )


def get_drop_lines(path: Path,
                   regexps: Sequence[re.Pattern],
                   known_tokens: Sequence[str],
                   keep_ratio=0.5,
                   normalize=True,
                   keep_sent_length=1) -> List[Tuple[int, float, str]]:
    """Returns a list of line number and lines which should be dropped given the criteria.
    Regexp defines a black-list of regular expressions.

    If normalized=True all non-words are removed from the sentence before counting the numer of words.\n
    If the remaining sentence contains any of the regexps it is DROPPED.\n
    If the remaining sentence has length less than or equal to keep_sent_length is it KEPT.\n
    If the keep_ratio is smaller or equal to the fraction of known_tokens in sentence it is KEPT.

    :param path: The pathlib.Path of the file to get the drop lines from.\n
    :param regexps: A black-list of regular expressions. If any is matched in a sentence, it is DROPPED.\n
    :param known_tokens: A whitelist of tokens which are considered as known.\n
    :param keep_ratio: If the fraction of known tokens is higher than keep_ration, the sentence is KEPT.\n
    :param normalize: If True, we first normalize the sentence by removing all words which contain non-words.\n
    :param keep_sent_length: If a sentence contains keep_sent_length of fewer words, it is KEPT.\n
    :return: A List of Tuples (the line number, the known fraction, the line).
    """
    drop_lines: List[Tuple[int, float, str]] = []
    with ProcessPoolExecutor(max_workers=THREADS) as executor:
        with path.open() as f_in:
            f_list = f_in.readlines()
            results = tqdm(executor.map(
                partial(should_drop,
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
                    drop_lines.append((index + 1, fraction, line))
    return drop_lines


def drop_lines(path: Path, out_path, lines_in: List[int]) -> bool:
    """Drops the given line numbers in a file. Words as a second step from "get_drop_lines()"

    :param path: The pathlib.Path of the file to drop the lines from.\n
    :param out_path: A pathlib.Path to write the result to.\n
    :param lines_in: A List of line numbers to drop.\n
    :return: True if successful.
    """
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