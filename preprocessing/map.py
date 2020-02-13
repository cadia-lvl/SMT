import pathlib
import logging
from concurrent.futures import ProcessPoolExecutor
from unicodedata import normalize
from re import sub, compile
from functools import partial

import click
from tqdm import tqdm

from src.util import (read_paracorpora_pickle,
                      ParaCorpora, Sentence, EnrichedCorpus, EnrichedSentence)

log = logging.getLogger()


# URI = re.compile(r"((http(s)?:\/\/)|(www)|([-a-zA-Z0-9:%_\+.~#?&/=]+?@))+([-a-zA-Z0-9@:%_\+.~#?&/=]+)", re.IGNORECASE)
# URI_SIMPLE = re.compile(r"([-a-zA-Z0-9@:%_\+.~#?&/=]+?)(\.is|\.com)", re.IGNORECASE)

# u'\u007c' - |
PIPE = compile(r"\u007c")
# u'\u003c', u'\u003e' - <, >
LT = compile(r"\u003c")
GT = compile(r"\u003e")
# u'\u005b', u'\u005d' - [, ]
BRACKET_OPEN = compile(r"\u005b")
BRACKET_CLOSE = compile(r"\u005d")

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


def low_norm(sent: Sentence) -> Sentence:
    return [normalize('NFKC', tok.casefold()) for tok in sent]


def apply_regexps(sent: Sentence, regexps) -> Sentence:
    for keywords in regexps:
        sent = [sub(string=tok, **keywords) for tok in sent]
    return sent


def process_sent(sentence: EnrichedSentence, form: bool, pos: bool, lemma: bool) -> str:
    if form:
        low_sent = low_norm(sentence[0])
        reg_sent = apply_regexps(low_sent, second_reg)
    if form and not pos and not lemma:
        return " ".join(reg_sent) + "\n"
    elif not form and not pos and lemma:
        return " ".join([f'{lemma}' for lemma in sentence[2]]) + "\n"
    elif form and pos and lemma:
        assert len(sentence[0]) == len(sentence[1]) == len(sentence[2])
        return " ".join([f'{form}|{pos}|{lemma}' for form, pos, lemma in zip(reg_sent, sentence[1], sentence[2])]) + "\n"
    else:
        raise NotImplementedError(f'form={form}, pos={pos}, lemma={lemma}')


def process_corpus(corpus: EnrichedCorpus,
                   lang: str,
                   p_out: pathlib.Path,
                   threads,
                   form,
                   pos,
                   lemma):
    with p_out.open('w+') as f_out:
        with ProcessPoolExecutor(max_workers=threads) as executor:
            results = tqdm(executor.map(
                partial(process_sent, form=form, pos=pos, lemma=lemma),
                corpus,
                chunksize=1000))
            for result in results:
                f_out.write(result)


@click.command()
@click.argument('pickle_file')
@click.argument('output_dir')
@click.option('--lemma', is_flag=True)
@click.option('--pos', is_flag=True)
@click.option('--form', is_flag=True)
@click.option('--lines', type=int)
@click.option('--threads', type=int, default=1)
def write(pickle_file,
          output_dir,
          lemma,
          pos,
          form,
          lines,
          threads):
    para_corpora: ParaCorpora = read_paracorpora_pickle(pickle_file)
    for lang in para_corpora.keys():
        log.info(f'Processing lang={lang}')
        for corpus_name in para_corpora[lang]:
            corpus_path = pathlib.Path(corpus_name)
            corpus: EnrichedCorpus = para_corpora[lang][corpus_name]
            target_file = pathlib.Path(output_dir).joinpath(
                f'{corpus_path.stem}{".form" if form else ""}{".pos" if pos else ""}{".lemma" if lemma else ""}.{lang}')
            log.info(f'Processing corpus={corpus_name} to target={target_file}')
            if lines != 0:
                corpus = corpus[:lines]
            process_corpus(corpus, lang, target_file, threads, form, pos, lemma)


@click.group()
def cli():
    pass


cli.add_command(write)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
    cli()
