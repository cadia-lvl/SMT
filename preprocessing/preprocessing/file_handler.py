import logging
import pickle
from typing import Union
from concurrent.futures import ProcessPoolExecutor
from functools import partial
import re

from tqdm import tqdm

from .types import (EnrichedCorpus, PCorpora, EnrichedPCorpora, Tokens)

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


def read_pickle(path: str) -> Union[PCorpora, EnrichedPCorpora]:
    with open(path, 'rb') as handle:
        return pickle.load(handle)


def write_pickle(pickle_out: str, corpora: Union[PCorpora, EnrichedPCorpora]) -> None:
    with open(pickle_out, '+wb') as handle:
        pickle.dump(corpora, handle, protocol=pickle.HIGHEST_PROTOCOL)


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
