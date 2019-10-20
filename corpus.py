""" # noqa: D213
Parallel corpus processing.

This module exposes some useful datatypes and functions to process parallel
corpora. The module is currently limted to EN and IS corpora.
"""
import os
import re
from unicodedata import normalize
from collections import Counter
from random import sample
from glob import glob
from os.path import getsize
from dataclasses import dataclass
from typing import Tuple, Optional, List, Dict, Iterable, Sequence, Union
from subprocess import run, PIPE, Popen
from enum import Enum

import tokenizer
import nltk
# Use full paths for ENV vars.
# Used to process .tmx files, required for this notebook
MOSES_SUITE = os.environ['MOSES_SUITE']
# The Moses system as pulled and built from github
MOSESDECODER = os.environ['MOSESDECODER']
# Systems used by Moses (see readme.md).
MOSESDECODER_TOOLS = os.environ['MOSESDECODER_TOOLS']

# This directory will be created and used for intermediary files.
WORKING_DIR = os.environ['WORKING_DIR']
# Some parts of the processing support threading, set the value here.
THREADS = os.environ['THREADS']


class Lang(Enum):
    """An enum for supported languages, based on strings"""  # noqa: D203
    EN = 'en'
    IS = 'is'


@dataclass(frozen=True)
class Corpus:
    """A datatype to handle corpus."""  # noqa: D203
    data_dir: str
    stage: str
    lang: Lang

    def get_corpus_info(self) -> Tuple[str, int, int]:
        size_MB = getsize(self.get_filepath()) >> 10
        line_count = _get_line_count(self.get_filepath())
        return (self.get_filepath(), size_MB, line_count)

    def get_corpus_info_formatted(self) -> str:
        path, size, lines = self.get_corpus_info()
        return f'{path:<40}{str(size)+"kB":^15}{lines:>10}'

    def get_filepath(self) -> str:
        return os.path.join(self.data_dir,
                            self.stage + '.' + self.lang.value)

    def get_filepath_wo_extension(self) -> str:
        return os.path.join(self.data_dir,
                            self.stage)


@dataclass(frozen=True)
class ParaCorpus:
    """  # noqa: D203
    A datatype to handle EN IS parallel corpus.
    """
    EN: Corpus
    IS: Corpus

    def get_filepath_wo_extension(self) -> str:
        stage = _get_stage((self.EN, self.IS))
        data_dir = _get_data_dir((self.EN, self.IS))
        return os.path.join(data_dir,
                            stage)


@dataclass(frozen=True)
class Model(Corpus):
    """ # noqa: D203
    A datatype to handle model configuration files. Is the same as Corpus.
    """


def from_para(other_para: ParaCorpus, new_stage: str) -> ParaCorpus:
    data_dir = _get_data_dir((other_para.EN, other_para.IS))
    return ParaCorpus(
        Corpus(data_dir,
               new_stage,
               Lang.EN),
        Corpus(data_dir,
               new_stage,
               Lang.IS)
    )


def _get_data_dir(corpora: Sequence[Corpus]) -> str:
    """ # noqa: D205
    Raises an exception if the sequence of Corpus does not have the same
    data dir otherwise returns the data_dir.
    """
    data_dir = set(corpus.data_dir for corpus in corpora)
    if len(data_dir) != 1:
        raise ValueError(f"Incorrect data_dir={data_dir}")
    return data_dir.pop()


def _get_lang(corpora: Sequence[Corpus]) -> Lang:
    """ # noqa: D205
    Raises an exception if the sequence of Corpus does not have the same
    lang otherwise returns the lang.
    """
    lang = set(corpus.lang for corpus in corpora)
    if len(lang) != 1:
        raise ValueError(f"Incorrect lang={lang}")
    return lang.pop()


def _get_stage(corpora: Sequence[Corpus]) -> str:
    """ # noqa: D205
    Raises an exception if the sequence of Corpus does not have the same
    stage otherwise returns the stage.
    """
    stage = set(corpus.stage for corpus in corpora)
    if len(stage) != 1:
        raise ValueError(f"Incorrect stage={stage}")
    return stage.pop()


def pipeline_load(data_dir: str,
                  stages: List[str],
                  langs: List[Lang] = [Lang.EN, Lang.IS]) \
        -> Dict[str, Union[ParaCorpus, Corpus, None]]:
    """Loads the processed pipeline as a dict from a directory given stages."""
    pipeline: Dict[str, Union[ParaCorpus, Corpus, None]] = dict()
    for stage in stages:
        files = {}
        for lang in langs:
            files[lang] = glob(f'{data_dir}/*{stage}*.{lang.value}')
        if all(len(files[key]) == 1 for key in files) and len(files) == 2:
            pipeline[stage] = ParaCorpus(
                Corpus(data_dir, stage, Lang.EN),
                Corpus(data_dir, stage, Lang.IS))
        elif all(len(files[key]) == 1 for key in files) and len(files) == 1:
            pipeline[stage] = Corpus(data_dir, stage, Lang.IS)
        else:
            pipeline[stage] = None
    return pipeline


def _get_line_count(filepath: str) -> int:
    """Count the number of new-lines in a file."""
    f = open(filepath, 'rb')
    lines = 0
    buf_size = 1024 * 1024
    read_f = f.raw.read  # type: ignore

    buf = read_f(buf_size)
    while buf:
        lines += buf.count(b'\n')
        buf = read_f(buf_size)

    return lines


def tmx_split(tmx_file_path: str, source: str, target: str) -> ParaCorpus:
    """Split a tmx file to ParaCorpus."""
    # This command creates two files in the same directory with .en, .is
    command = ['python2',
               f'{MOSES_SUITE}/src/corpus-tools/tmx2txt.py',
               '-D',
               tmx_file_path,
               source,
               target,
               ]
    run(command, check=True)
    data_dir = os.path.dirname(tmx_file_path)
    # We assume that the filename has the pattern "filename.extension"
    stage = os.path.basename(tmx_file_path).split('.')[0]
    return ParaCorpus(
        Corpus(data_dir, stage, Lang.EN),
        Corpus(data_dir, stage, Lang.IS)
    )


def corpus_peek(corpus: Corpus, length: int = 10) -> Iterable[str]:
    """Returns the first length many lines from a given corpus."""
    with open(corpus.get_filepath()) as f:
        index = 0
        for line in f:
            index += 1
            yield line
            if index == length:
                return


def p_corpus_peek(corpus: ParaCorpus, length: int = 10) \
        -> Iterable[str]:
    """ # noqa: D205
    Returns a generator of formatted strings of the first length lines of a
    ParaCorpus."""
    en_corpus = corpus_peek(corpus.EN, length)
    is_corpus = corpus_peek(corpus.IS, length)
    for en_sent, is_sent in zip(en_corpus, is_corpus):
        yield f'EN: {en_sent} IS: {is_sent}'


def corpus_combine(corpora: List[Corpus], stage: str) -> Corpus:
    """# noqa: D205
    Combines a collection of Corpus to a single Corpus.

    The output Corpusgets written over if run multiple times.
    Ensures that all corpora are from the same directory and of the same language.
    """
    source_filepaths = (corpus.get_filepath() for corpus in corpora)
    lang = _get_lang(corpora)
    data_dir = _get_data_dir(corpora)
    target_corpus = Corpus(data_dir,
                           stage,
                           lang)
    command = ['cat'] + list(source_filepaths)
    with open(target_corpus.get_filepath(), 'w+') as out:
        run(command, stdout=out, check=True)

    return target_corpus


def corpus_split(corpus: Corpus,
                 stages: Tuple[str, str],
                 count: int) -> Tuple[Corpus, Corpus]:
    """ # noqa: D205
    Splits a Corpus to two Corpus with stages. The latter stage has count
    many lines
    """
    first_stage = Corpus(
        corpus.data_dir,
        stages[0],
        corpus.lang
    )
    second_stage = Corpus(
        corpus.data_dir,
        stages[1],
        corpus.lang
    )
    with open(corpus.get_filepath()) as f_in:
        lines = f_in.readlines()
        with open(first_stage.get_filepath(), 'w+') as f_s1, \
                open(second_stage.get_filepath(), 'w+') as f_s2:
            f_s1.writelines(lines[:-count])
            f_s2.writelines(lines[-count:])

    return (first_stage, second_stage)


def corpus_length_fix(corpus: ParaCorpus, stage: str,
                      min_length: int, max_length: int) -> ParaCorpus:
    """ # noqa: D205
    Consolidates the lengths of a ParaCorpus to min, max lengths provided.

    Also removes empty lines (from either side). Returns a new ParaCorpus.
    """
    target_corpus = from_para(corpus, stage)
    command = [f'{MOSESDECODER}/scripts/training/clean-corpus-n.perl',
               corpus.get_filepath_wo_extension(),
               Lang.EN.value,
               Lang.IS.value,
               target_corpus.get_filepath_wo_extension(),
               str(min_length),
               str(max_length)]
    run(command, check=True)
    return target_corpus


def sent_regexp(corpus: str, regexps: List[Tuple[str, str]]) -> str:
    """ # noqa: D205
    Applies a list of regular expressions and their substitions to a string.
    """
    processed_line = corpus
    for regular_expression, sub_string in regexps:
        processed_line = re.sub(
            regular_expression, sub_string, processed_line)
    return processed_line


def corpus_regexp(corpus: Corpus,
                  stage: str,
                  regexps: List[Tuple[str, str]]) -> Corpus:
    """ # noqa: D205
    Applies a list of regular expressions and their substitions to a Corpus and
    returns the processed corpus.
    """
    target_corpus = Corpus(
        corpus.data_dir,
        stage,
        corpus.lang
    )
    # We delete the file if it exists.
    try:
        os.remove(target_corpus.get_filepath())
    except OSError:
        pass
    for line in corpus_peek(corpus, length=0):
        processed_line = sent_regexp(line, regexps)
        with open(target_corpus.get_filepath(), 'a+') as f:
            f.write(processed_line)
    return target_corpus


def corpus_shuffle(corpus: Corpus, seed_file: str, stage: str) -> Corpus:
    """ # noqa: D205
    Shuffles a Corpus using the input as a random seed. Returns the shuffled
    Corpus.
    """
    target_corpus = Corpus(
        corpus.data_dir,
        stage,
        corpus.lang
    )
    command = [
        'shuf',
        f'--random-source={seed_file}',
        f'{corpus.get_filepath()}'
    ]
    with open(target_corpus.get_filepath(), 'w+') as out:
        run(command, stdout=out, check=True)
    return target_corpus


def corpus_sample(corpus: Corpus, count: int) -> Iterable[str]:
    """Samples count many lines from a Corpus."""
    with open(corpus.get_filepath()) as f_in:
        # Careful, we read the whole file...
        lines = f_in.readlines()
    yield from sample(lines, count)


def corpus_sentence_counter(corpus: Corpus) -> Counter:
    """Returns a Counter with the sentence length as key and the count as value."""
    with open(corpus.get_filepath()) as f_in:
        counter: Counter = Counter()
        for line in f_in:
            sent_length = len(line.split(" "))
            counter[sent_length] += 1
    return counter


def corpus_token_counter(corpus: Corpus) -> Counter:
    """Returns a Counter with the token as key and the count as value."""
    with open(corpus.get_filepath()) as f_in:
        counter: Counter = Counter()
        for line in f_in:
            counter.update(line.strip('\n').split(" "))
    return counter


def sent_lowercase_normalize(sent: str) -> str:
    """Applies unicode lowercase and normalize on a string."""
    return normalize('NFKC', sent.casefold())


def corpus_lowercase_normalize(corpus: Corpus, stage: str) -> Corpus:
    """Applies unicode lowercase and normalize on a Corpus."""
    target_corpus = Corpus(
        corpus.data_dir,
        stage,
        corpus.lang
    )
    with open(corpus.get_filepath()) as f_in, \
            open(target_corpus.get_filepath(), 'w+') as f_out:
        for line in f_in:
            f_out.write(sent_lowercase_normalize(line))
    return target_corpus


def corpus_tokenize(corpus: Corpus, stage: str, method: str = 'pass-through') -> Corpus:
    """ # noqa D205
    Tokenizes a Corpus using the specified method. Returns the tokenized
    Corpus.
    Supported methods for IS (only):
        IS(default): "pass-through", basic tokenization.
        IS: "placeholders", uses placeholders for some NEs.
    """
    target_corpus = Corpus(
        corpus.data_dir,
        stage,
        corpus.lang
    )
    with open(corpus.get_filepath()) as f_in, \
            open(target_corpus.get_filepath(), 'w+') as f_out:
        for line in f_in:
            tokenized_sent = sent_tokenize(line,
                                           corpus.lang,
                                           method)
            # And add a newline when we write it out
            f_out.write(tokenized_sent + '\n')
    return target_corpus


def sent_tokenize(sentence, lang: Lang, method: str = 'pass-through'):
    """ # noqa D205
    Tokenizes a sentence using the specified method. Returns the tokenized
    sentence.
    Supported methods for IS (only):
        IS(default): "pass-through", basic tokenization.
        IS: "placeholders", uses placeholders for some NEs.
    """
    if lang == Lang.EN:
        # We use the word_tokenize NLTL tokenizer for english
        return " ".join(nltk.word_tokenize(sentence))
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
    return " ".join(result)


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


def corpus_truecase_train(corpus: Corpus, stage: str) -> Model:
    """Trains a truecase model on the Corpus and returns a Model."""
    target_model = Model(
        corpus.data_dir,
        stage,
        corpus.lang
    )
    command = [f'{MOSESDECODER}/scripts/recaser/train-truecaser.perl',
               '--model',
               target_model.get_filepath(),
               '--corpus',
               corpus.get_filepath()
               ]
    run(command)
    return target_model


def corpus_truecase_apply(corpus: Corpus, truecase_model: Model, stage: str) -> Corpus:
    """Applies a given truecase Model to a Corpus, returns truecased Corpus."""
    target_corpus = Corpus(
        corpus.data_dir,
        stage,
        corpus.lang
    )
    command = [f'{MOSESDECODER}/scripts/recaser/truecase.perl',
               '--model',
               truecase_model.get_filepath()
               ]
    with open(corpus.get_filepath()) as f_in, \
            open(target_corpus.get_filepath(), 'w+') as f_out:
        run(command, stdout=f_out, stdin=f_in, check=True)
    return target_corpus


def sent_truecase(sentence: str, truecase_model: Model):
    """Truecases a given sentence. Assumes no newlines are in the sentence."""
    p1 = Popen(["echo", sentence], stdout=PIPE)
    p2 = Popen([f'{MOSESDECODER}/scripts/recaser/truecase.perl',
                '--model',
                truecase_model.get_filepath()
                ],
               stdin=p1.stdout,
               stdout=PIPE)
    p1.stdout.close()
    output = p2.communicate()[0].decode("utf-8").replace('\n', '')
    return output


def kenlm_create(corpus: Corpus, stage: str, order: int) -> Model:
    """Creates a KenLM language model of order. Binarizes the model."""
    tmp_model = Model(
        corpus.data_dir,
        f'arpa',
        corpus.lang
    )
    command = [f'{MOSESDECODER}/bin/lmplz',
               '-o',
               str(order),
               '-S',
               '50%'
               ]
    with open(corpus.get_filepath()) as f_in, \
            open(tmp_model.get_filepath(), 'w+') as f_out:
        run(command, stdout=f_out, stdin=f_in, check=True)
    target_model = Model(
        corpus.data_dir,
        stage,
        corpus.lang
    )
    command = [f'{MOSESDECODER}/bin/build_binary',
               '-S',
               '50%',
               tmp_model.get_filepath(),
               target_model.get_filepath()
               ]
    run(command, check=True)
    return target_model


def kenlm_eval(model: Model, sentence: str) -> str:
    p1 = Popen(["echo", sentence], stdout=PIPE)
    p2 = Popen([f'{MOSESDECODER}/bin/query',
                model.get_filepath()
                ],
               stdin=p1.stdout,
               stdout=PIPE)
    p1.stdout.close()
    output = p2.communicate()[0].decode("utf-8")
    return output
