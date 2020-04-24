import logging
import pathlib
from typing import List
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import itertools
from xml.etree import ElementTree as ET

from tqdm import tqdm

from .types import (iCorpus, iTokCorpus, EnrichedCorpus, EnrichedSentence)
from preprocessing import pipeline

log = logging.getLogger()


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


def make_batches(sequence, batch_size: int):
    sourceiter = iter(sequence)
    while True:
        try:
            batchiter = itertools.islice(sourceiter, int(batch_size))
            yield itertools.chain([next(batchiter)], batchiter)
        except StopIteration:
            return


def get_kvistur_resources():
    return {
        "modifiers": str(pathlib.Path(__file__).resolve().parent.parent.joinpath('kvistur').joinpath('resources').joinpath('modifiers.dawg')),
        "heads": str(pathlib.Path(__file__).resolve().parent.parent.joinpath('kvistur').joinpath('resources').joinpath('heads.dawg')),
        "templates": str(pathlib.Path(__file__).resolve().parent.parent.joinpath('kvistur').joinpath('resources').joinpath('templates.dawg')),
        "splits": str(pathlib.Path(__file__).resolve().parent.parent.joinpath('kvistur').joinpath('resources').joinpath('splits.dawg')),
    }


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
        results = tqdm(executor.map(
            read_rmh_file,
            files,
            chunksize=chunksize))
        for result in results:
            yield from result


def write_moses(corpus: EnrichedCorpus, output_file, threads: int, chunksize: int, write_form: bool, write_pos: bool, write_lemma: bool) -> None:
    with open(output_file, 'w+') as f_out:
        with ProcessPoolExecutor(max_workers=threads) as executor:
            results = tqdm(executor.map(
                partial(get_moses_line, write_form=write_form, write_pos=write_pos, write_lemma=write_lemma),
                corpus,
                chunksize=chunksize))
            for result in results:
                f_out.write(result)


def get_moses_line(line: EnrichedSentence, write_form: bool, write_pos: bool, write_lemma: bool) -> str:
    form, pos, lemma = line
    if write_form:
        form = list(pipeline.escape_moses_chars((token for token in form)))
    if write_pos:
        pos = list(pipeline.escape_moses_chars((token for token in pos)))
    if write_lemma:
        lemma = list(pipeline.escape_moses_chars((token for token in lemma)))
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
