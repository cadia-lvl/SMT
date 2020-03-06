import pathlib
import logging
import random
from typing import cast

import click

from preprocessing.file_handler import write_pickle, read_pickle, write_moses
from preprocessing import pipeline
from preprocessing.types import (PCorpora, EnrichedPCorpora)

log = logging.getLogger()


def _get_sample(p_corpora, sample_size):
    indices = random.sample(range(0, len(p_corpora['en'])), k=sample_size)
    for index in indices:
        yield (p_corpora['is'][index], p_corpora['en'][index])


@click.command()
@click.argument('pickle_in')
@click.argument('lang')
@click.argument('save_to', type=str)
@click.option('--lemma', is_flag=True)
@click.option('--pos', is_flag=True)
@click.option('--form', is_flag=True)
@click.option('--lines', type=int)
@click.option('--threads', type=int, default=1)
@click.option('--chunksize', type=int, default=4000)
def write(pickle_in, lang, save_to, lemma, pos, form, lines, threads, chunksize):
    log.info(f'Reading pickle={pickle_in}, lang={lang}')
    p_corpora: EnrichedPCorpora = read_pickle(pickle_in)
    log.info(f'Writing file={save_to}')
    write_moses(p_corpora[lang], output_file=save_to, threads=threads, chunksize=chunksize, write_form=form, write_pos=pos, write_lemma=lemma)


@click.command()
@click.argument('pickle_in')
@click.option('--sample_size', type=int, default=1)
def sample(pickle_in, sample_size):
    log.info(f'Reading pickle={pickle_in}')
    p_corpora: EnrichedPCorpora = read_pickle(pickle_in)
    assert len(p_corpora['en']) == len(p_corpora['is'])
    while not input("Press ENTER to continue"):
        for is_sample, en_sample in _get_sample(p_corpora, sample_size=sample_size):
            log.info(f'IS: {is_sample}EN: {en_sample}')


@click.command()
@click.argument('pickle_in')
@click.argument('save_to_prefix', type=str, default='truecase-model')
@click.option('--segment', type=str, default='form', help='Part of the EnrichedPCorpus to train on.')
@click.option('--threads', type=int, default=1)
def train_truecase(pickle_in, save_to_prefix, segment, threads):
    """Trains two Moses truecase models, one for each language, and saves the model to {save_to_prefix}.{segment}.{lang}. Works on EnrichedPCorpora."""
    log.info(f'Reading pickle={pickle_in}')
    p_corpora: EnrichedPCorpora = read_pickle(pickle_in)
    index = pipeline.get_index_of_segment(segment=segment)
    for lang in p_corpora:
        save_to = f'{save_to_prefix}.{segment}.{lang}'
        log.info(f'save_to={save_to}')
        pipeline.train_truecase([lines[index] for lines in p_corpora[lang]], save_to=save_to, threads=threads)
    log.info('Done.')


@click.command()
@click.argument('pickle_in')
@click.argument('pickle_out')
@click.argument('load_from')
@click.option('--lang', type=str, default='en')
@click.option('--segment', type=str, default='form', help='Part of the EnrichedPCorpus to apply to.')
def truecase(pickle_in, pickle_out, load_from, lang, segment):
    log.info(f'Reading pickle={pickle_in}')
    p_corpora: EnrichedPCorpora = read_pickle(pickle_in)
    p_corpora[lang] = pipeline.truecase_enriched_corpus(p_corpora[lang], load_from=load_from, segment=segment)
    log.info(f'Writing pickle={pickle_out}')
    write_pickle(pickle_out, p_corpora)


@click.command()
@click.argument('pickle_in')
@click.argument('pickle_out_train')
@click.argument('pickle_out_test')
@click.option('--test_size', type=int, default=2000)
@click.option('--shuffle/--no-shuffle', default=True)
@click.option('--seed', type=int, default=42)
def split(pickle_in, pickle_out_train, pickle_out_test, test_size, shuffle, seed):
    log.info(f'Reading pickle={pickle_in}')
    p_corpora: EnrichedPCorpora = read_pickle(pickle_in)
    train, test = pipeline.split_corpora(p_corpora, test_size=test_size, shuffle=shuffle, seed=seed)
    write_pickle(pickle_out_train, train)
    write_pickle(pickle_out_test, test)
    log.info('Done.')


@click.command()
@click.argument('p_en', type=click.File(mode='r', lazy=True))
@click.argument('p_is', type=click.File(mode='r', lazy=True))
@click.argument('pickle_out', type=click.Path())
def read_p_corpora_to_pickle(p_en, p_is, pickle_out):
    en_path = pathlib.Path(p_en.name)
    is_path = pathlib.Path(p_is.name)
    log.info(f'Reading en={en_path}, is={is_path} to pickle={pickle_out}')
    para: PCorpora = {
        'en': [sent for sent in p_en],
        'is': [sent for sent in p_is]
    }
    write_pickle(pickle_out, para)
    log.info('Done.')


@click.command()
@click.argument('pickle_in')
@click.argument('pickle_out')
@click.option('--chunksize', type=int, default=4000, help="Number of lines to process at once.")
@click.option('--lines', type=int, default=0, help="For debugging, limit processing to x lines per corpus. 0 for all.")
def enrich(pickle_in, pickle_out, chunksize: int, lines: int):
    # We assume a PCorpora has been given.
    p_corpora = cast(PCorpora, read_pickle(pickle_in))
    write_pickle(pickle_out, pipeline.enrich_p_corpora(p_corpora, chunksize=chunksize, lines=lines))


@click.command()
@click.argument('file_in')
@click.argument('file_out')
@click.argument('lang')
def detokenize(file_in, file_out, lang):
    with open(file_in) as f_in, open(file_out, mode='w+') as f_out:
        log.info(f'Reading={file_in}, writing={file_out}')
        for line in f_in:
            f_out.write(pipeline.detokenize(line=line, lang=lang) + '\n')
    log.info('Done.')


@click.group()
def cli():
    pass


cli.add_command(read_p_corpora_to_pickle)
cli.add_command(enrich)
cli.add_command(sample)
cli.add_command(train_truecase)
cli.add_command(truecase)
cli.add_command(split)
cli.add_command(write)
cli.add_command(detokenize)

if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
    cli()
