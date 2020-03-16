import logging
import pickle
from typing import Union, List, Dict
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import itertools
import re
from xml.etree import ElementTree as ET

from tqdm import tqdm
import ujson

from .types import (iCorpus, iTokCorpus, EnrichedCorpus, PCorpora, EnrichedPCorpora, Tokens)

log = logging.getLogger()

# u'\u007c' - |
PIPE = re.compile(r"\u007c")
# u'\u003c', u'\u003e' - <, >
LT = re.compile(r"\u003c")
GT = re.compile(r"\u003e")
# u'\u005b', u'\u005d' - [, ]
BRACKET_OPEN = re.compile(r"\u005b")
BRACKET_CLOSE = re.compile(r"\u005d")

second_reg = [
    {
        'pattern': PIPE,
        'repl': '_pipe_'
    },
    {
        'pattern': LT,
        'repl': '_lt_'
    },
    {
        'pattern': GT,
        'repl': '_gt_'
    },
    {
        'pattern': BRACKET_OPEN,
        'repl': '_bo_'
    },
    {
        'pattern': BRACKET_CLOSE,
        'repl': '_bc_'
    }
]


def serialize(path: str, corpus: iCorpus):
    """We use plain files"""
    log.info(f'Writing txt={path}')
    with open(path, 'w+') as f_out:
        for line in corpus:
            f_out.write(line)


def deserialize(path: str) -> iCorpus:
    """We use plain files"""
    log.info(f'Reading txt={path}')
    with open(path) as f_in:
        for line in f_in:
            yield line


def read_json(path: str) -> Dict:
    log.info(f'Reading json={path}')
    with open(path, 'r') as f_in:
        return ujson.load(f_in)


def write_json(path: str, corpus: Union[Dict, List]) -> None:
    log.info(f'Writing json={path}')
    with open(path, '+w') as f_out:
        ujson.dump(corpus, f_out)


def read_pickle(path: str) -> Union[PCorpora, EnrichedPCorpora]:
    log.info(f'Reading pickle={path}')
    with open(path, 'rb') as handle:
        return pickle.load(handle)


def write_pickle(path: str, corpora: Union[PCorpora, EnrichedPCorpora]) -> None:
    log.info(f'Writing pickle={path}')
    with open(path, '+wb') as handle:
        pickle.dump(corpora, handle, protocol=pickle.HIGHEST_PROTOCOL)


def make_batches(sequence, batch_size: int, max_lines=0):
    sourceiter = iter(sequence)
    while True:
        batchiter = itertools.islice(sourceiter, batch_size)
        yield itertools.chain([batchiter.next()], batchiter)


def read_rmh_file(path: str):
    """
    Reads a single RMH file and returns a TokCorpus.

    Adjusted code from xml_tools.py from Róbert Kjaran <robert@kjaran.com>
    """
    log.debug(f'Processing file={path}')
    NS = {'a': 'http://www.tei-c.org/ns/1.0'}
    root = ET.parse(str(path)).getroot()
    # We gather all the paragraphs from the body, avoiding the divs
    return [tuple((token_node.text for token_node in sentence_node.findall('./*') if token_node.text is not None))
            for paragraph_node in root.findall('.//a:body//a:p', NS)
            for sentence_node in paragraph_node.findall('.//a:s', NS)]


def rmh_2_corpus(files: List[str], threads=1, chunksize=100) -> iTokCorpus:
    """
    Reads RMH files and extracts the tokens, including punctuations. Returns a TokCorpus.

    Multiple threads are used to process batches (of size chunksize) of files together.
    """
    with ProcessPoolExecutor(max_workers=threads) as executor:
        return tqdm(executor.map(
            read_rmh_file,
            files,
            chunksize=chunksize))


def apply_regexps(sent: Tokens, regexps) -> Tokens:
    for keywords in regexps:
        sent = [re.sub(string=tok, **keywords) for tok in sent]
    return sent


def write_moses(corpus: EnrichedCorpus, output_file, threads: int, chunksize: int, write_form: bool, write_pos: bool, write_lemma: bool) -> None:
    with open(output_file, 'w+') as f_out:
        with ProcessPoolExecutor(max_workers=threads) as executor:
            results = tqdm(executor.map(
                partial(get_moses_line, write_form=write_form, write_pos=write_pos, write_lemma=write_lemma),
                corpus,
                chunksize=chunksize))
            for result in results:
                f_out.write(result)


def get_moses_line(line, write_form: bool, write_pos: bool, write_lemma: bool) -> str:
    form, pos, lemma = line
    if write_form:
        form = apply_regexps(form, second_reg)
    if write_pos:
        pos = apply_regexps(pos, second_reg)
    if write_lemma:
        lemma = apply_regexps(lemma, second_reg)
    # Only form
    if write_form and not write_pos and not write_lemma:
        return " ".join(form) + "\n"
    # Only lemma
    elif not write_form and not write_pos and write_lemma:
        return " ".join(lemma) + "\n"
    # Only pos
    elif not write_form and write_pos and not write_lemma:
        return " ".join(pos) + "\n"
    # All
    elif write_form and write_pos and write_lemma:
        assert len(form) == len(pos) == len(lemma)
        return " ".join([f'{form}|{pos}|{lemma}' for form, pos, lemma in zip(form, pos, lemma)]) + "\n"
    else:
        raise NotImplementedError(f'form={write_form}, pos={write_pos}, lemma={write_lemma}')
