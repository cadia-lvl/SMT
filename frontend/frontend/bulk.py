"""
Bulk processing of sentences. Uses functions defined in core.py and supports multiprocessing.
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
# A dict to map between "ISO 639-1-ISO 3166-1" to ISO 639-1 (two letter language code)

TMX_2_LANG: Dict[str, Lang] = {
    'EN-GB': Lang.EN,
    'IS-IS': Lang.IS
}

# Some parts of the processing support threading, set the value here.
THREADS = int(os.environ.get('THREADS', 4))
CHUNKSIZE = 4000


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
    """Returns the path, size and line count of a Path."""
    size = _sizeof_fmt(path.stat().st_size)
    line_count = _get_line_count(path.resolve())
    return str(path.resolve()), size, line_count


def info_formatted(path: Path) -> str:
    """Returns the formatted path, size and line count of a Path."""
    path_s, size, lines = info(path)
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
            print(info_formatted(result))
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


def peeks(paths: List[Path], length: int = 10) -> Iterator[str]:
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
                       partial(c_regexp, regexps=regexps)
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


def lowercase_normalize(path: Path,
                        out_path: Path) -> bool:
    """ # noqa: D205
    Applies unicode lowercase and normalize on a Path. Writes the
    result to out_path. Returns True if successful.
    """
    return in_parallel(path,
                       out_path,
                       THREADS,
                       c_lower_norm)


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
    tok = get_tokenizer(_lang(path), method)
    return in_parallel(path,
                       out_path,
                       THREADS,
                       partial(apply_tokenizer, tokenizer=tok)
                       )


def get_drop_lines(path: Path,  # pylint: disable=too-many-arguments,too-many-locals
                   regexps: Sequence[re.Pattern],
                   known_tokens: Sequence[str],
                   keep_ratio=0.5,
                   normalize=True,
                   keep_sent_length=1) -> List[Tuple[int, float, str]]:
    """ # noqa: D205
    Returns a list of line number and lines which should be dropped.

    If normalized=True all non-words (\d\W_) are removed from the sentence.
    If the remaining sentence contains any of the regexps it is DROPPED.
    If the remaining sentence has length less than or equal to keep_sent_length
    is it KEPT.
    If the keep_ratio is smaller or equal to the fraction of known_tokens in
    sentence it is KEPT.
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