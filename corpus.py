"""Parallel corpus processing."""
import os
from glob import glob
from os.path import getsize
from dataclasses import dataclass
from typing import Tuple, Set, Optional, List, Dict
from subprocess import run
from enum import Enum

# Use full paths for ENV vars.
# Used to process .tmx files, required for this notebook
MOSES_SUITE = os.environ['MOSES_SUITE']
# The Moses system as pulled and built from github
MOSESDECODER = os.environ['MOSESDECODER']
# Systems used by Moses (see readme.md).
MOSESDECODER_TOOLS = os.environ['MOSESDECODER_TOOLS']

# This directory will be created and used for intermediary files.
WORKING_DIR = os.environ['WORKING_DIR']
# This directory will be created and used for the generated models.
MODEL_DIR = os.environ['MODEL_DIR']
# Some parts of the processing support threading, set the value here.
THREADS = os.environ['THREADS']


class Lang(Enum):
    """An enum for supported languages, based on strings""" # noqa: D203
    EN = 'en'
    IS = 'is'

@dataclass(frozen=True)
class Corpus:
    """A datatype to handle corpus.""" # noqa: D203
    filepath: str
    lang: Lang

    def get_corpus_info(self) -> Tuple[str, int, int]:
        size_MB = getsize(self.filepath) >> 20
        line_count = get_line_count(self.filepath)
        return (self.filepath, size_MB, line_count)


# A general ParallelCorpus type. Not much used.
ParaCorpus = Tuple[Corpus, Corpus]


@dataclass(frozen=True)
class ENISParaCorpus:
    """A datatype to handle EN IS parallel corpus.""" # noqa: D203
    EN: Corpus
    IS: Corpus


def toENISParaCorpus(para_corpus: ParaCorpus) -> ENISParaCorpus:
    """Maps ParaCorpus to ENISParaCorpus."""
    en_corpus = None
    is_corpus = None
    for corpus in para_corpus:
        if corpus.lang == Lang.EN:
            en_corpus = corpus
        elif corpus.lang == Lang.IS:
            is_corpus = corpus
        else:
            raise ValueError(f"Unsupported lang={corpus.lang}")
    if en_corpus is not None and is_corpus is not None:
        return ENISParaCorpus(en_corpus, is_corpus)

    raise ValueError("Unable to unpack ParaCorpus to ENISParaCorpus")


def get_filepath(target_dir: str, stage: str, lang: Lang) -> str:
    """Returns a new filepath given the target_dir, stage and lang."""
    return f'{target_dir}/{stage}.{lang.value}'


def load_en_is_pipeline_from_stages(data_dir: str, stages: List[str]) \
        -> Dict[str, Optional[ENISParaCorpus]]:
    """Loads the processed pipeline as a dict from a directory given stages."""
    pipeline: Dict[str, Optional[ENISParaCorpus]] = dict()
    for stage in stages:
        en_files = glob(f'{data_dir}/*{stage}*.{Lang.EN.value}')
        is_files = glob(f'{data_dir}/*{stage}*.{Lang.IS.value}')
        if len(en_files) == 1 and len(is_files) == 1:
            pipeline[stage] = ENISParaCorpus(
                Corpus(en_files[0], Lang.EN),
                Corpus(is_files[0], Lang.IS))
        elif not en_files and not is_files:
            pipeline[stage] = None
        else:
            raise Exception(f"Unable to gather files for stage={stage},\
                            en={en_files}, is={is_files}")
    return pipeline


def get_line_count(filepath: str) -> int:
    """Count the number of new-lines in a file."""
    f = open(filepath, 'rb')
    lines = 0
    buf_size = 1024 * 1024
    read_f = f.raw.read # type: ignore 

    buf = read_f(buf_size)
    while buf:
        lines += buf.count(b'\n')
        buf = read_f(buf_size)

    return lines


def split_tmx(tmx_file_path: str) -> ParaCorpus:
    """Split a tmx file to ParaCorpus."""
    command = ['python2',
               f'{MOSES_SUITE}/src/corpus-tools/tmx2txt.py',
               '-D',
               tmx_file_path,
               'EN-GB',
               'IS-IS'
               ]
    run(command)
    return (
        Corpus(tmx_file_path.replace(r'tmx', Lang.EN.value), Lang.EN),
        Corpus(tmx_file_path.replace(r'tmx', Lang.IS.value), Lang.IS)
    )


def combine_corpora(corpora: Set[Corpus], destination_filepath, lang_id) -> Corpus:
    """Combines a collection of Corpus to a single Corpus. The output Corpus gets written over if run multiple times."""
    source_filepaths = (corpus.filepath for corpus in corpora)
    target_file_corpora = Corpus(destination_filepath,
                                 lang_id)
    command = ['cat'] + list(source_filepaths)
    with open(destination_filepath, 'w') as out:
        run(command, stdout=out)

    return target_file_corpora
