import pathlib
import logging
import random
from typing import cast
from glob import glob

import click

from preprocessing import file_handler
from preprocessing import pipeline
from preprocessing.types import (PCorpora, EnrichedPCorpora, TokCorpus)

log = logging.getLogger()


def _get_sample(p_corpora, sample_size):
    indices = random.sample(range(0, len(p_corpora['en'])), k=sample_size)
    for index in indices:
        yield (p_corpora['is'][index], p_corpora['en'][index])


@click.command()
@click.argument('data_in')
@click.argument('lang')
@click.argument('save_to', type=str)
@click.option('--lemma', is_flag=True)
@click.option('--pos', is_flag=True)
@click.option('--form', is_flag=True)
@click.option('--lines', type=int)
@click.option('--threads', type=int, default=1)
@click.option('--chunksize', type=int, default=4000)
def write(data_in, lang, save_to, lemma, pos, form, lines, threads, chunksize):
    p_corpora: EnrichedPCorpora = file_handler.deserialize(data_in)
    file_handler.write_moses(p_corpora[lang], output_file=save_to, threads=threads, chunksize=chunksize, write_form=form, write_pos=pos, write_lemma=lemma)


@click.command()
@click.argument('data_in')
@click.option('--sample_size', type=int, default=1)
def sample(data_in, sample_size):
    p_corpora: EnrichedPCorpora = file_handler.deserialize(data_in)
    assert len(p_corpora['en']) == len(p_corpora['is'])
    while not input("Press ENTER to continue"):
        for is_sample, en_sample in _get_sample(p_corpora, sample_size=sample_size):
            log.info(f'IS: {is_sample}EN: {en_sample}')


@click.command()
@click.argument('data_in')
@click.argument('save_to_prefix', type=str, default='truecase-model')
@click.option('--segment', type=str, default='form', help='Part of the EnrichedPCorpus to train on.')
@click.option('--threads', type=int, default=1)
def train_truecase(data_in, save_to_prefix, segment, threads):
    """Trains two Moses truecase models, one for each language, and saves the model to {save_to_prefix}.{segment}.{lang}. Works on EnrichedPCorpora."""
    p_corpora: EnrichedPCorpora = file_handler.deserialize(data_in)
    index = pipeline.get_index_of_segment(segment=segment)
    for lang in p_corpora:
        save_to = f'{save_to_prefix}.{segment}.{lang}'
        log.info(f'save_to={save_to}')
        pipeline.train_truecase([lines[index] for lines in p_corpora[lang]], save_to=save_to, threads=threads)
    log.info('Done.')


@click.command()
@click.argument('data_in')
@click.argument('data_out')
@click.argument('load_from')
@click.option('--lang', type=str, default='en')
@click.option('--segment', type=str, default='form', help='Part of the EnrichedPCorpus to apply to.')
def truecase(data_in, data_out, load_from, lang, segment):
    p_corpora: EnrichedPCorpora = file_handler.deserialize(data_in)
    p_corpora[lang] = pipeline.truecase_enriched_corpus(p_corpora[lang], load_from=load_from, segment=segment)
    file_handler.serialize(data_out, p_corpora)


@click.command()
@click.argument('data_in')
@click.argument('data_out_train')
@click.argument('data_out_test')
@click.option('--test_size', type=int, default=2000)
@click.option('--shuffle/--no-shuffle', default=True)
@click.option('--seed', type=int, default=42)
def split(data_in, data_out_train, data_out_test, test_size, shuffle, seed):
    p_corpora: EnrichedPCorpora = file_handler.deserialize(data_in)
    train, test = pipeline.split_corpora(p_corpora, test_size=test_size, shuffle=shuffle, seed=seed)
    file_handler.serialize(data_out_train, train)
    file_handler.serialize(data_out_test, test)
    log.info('Done.')


@click.command()
@click.argument('p_en', type=click.File(mode='r', lazy=True))
@click.argument('p_is', type=click.File(mode='r', lazy=True))
@click.argument('data_out', type=click.Path())
def read_p_corpora_to_pickle(p_en, p_is, data_out):
    en_path = pathlib.Path(p_en.name)
    is_path = pathlib.Path(p_is.name)
    log.info(f'Reading en={en_path}, is={is_path} to pickle={data_out}')
    para: PCorpora = {
        'en': [sent for sent in p_en],
        'is': [sent for sent in p_is]
    }
    file_handler.serialize(data_out, para)
    log.info('Done.')


@click.command()
@click.argument('data_in')
@click.argument('data_out')
@click.option('--chunksize', type=int, default=4000, help="Number of lines to process at once.")
@click.option('--lines', type=int, default=0, help="For debugging, limit processing to x lines per corpus. 0 for all.")
def enrich(data_in, data_out, chunksize: int, lines: int):
    # We assume a PCorpora has been given.
    p_corpora = cast(PCorpora, file_handler.deserialize(data_in))
    file_handler.serialize(data_out, pipeline.enrich_p_corpora(p_corpora, chunksize=chunksize, lines=lines))


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


@click.command()
@click.argument('files_in', nargs=-1)
@click.argument('file_out')
def deduplicate(files_in, file_out):
    known_sent = set()
    for file_in in files_in:
        corpus = cast(TokCorpus, file_handler.deserialize(file_in))
        log.info('Deduplicating')
        known_sent.update(pipeline.deduplicate(corpus, known=known_sent))

    file_handler.serialize(file_out, known_sent)
    log.info('Done.')


@click.command()
@click.argument('dir')
@click.argument('file_out')
@click.option('--threads', type=int, default=1, help="Number of threads to use.")
@click.option('--chunksize', type=int, default=400, help="Number of files to process per thread.")
def read_rmh(dir, file_out, threads, chunksize):
    """
    Reads a directory and globs all .xml files (removing hdr files) and extracts all texts. Tailored to RMH .tei format reading.
    Writes the output to .json.
    """
    files = [xml_file for xml_file in glob(f'{dir}/**/*.xml', recursive=True) if not (xml_file.endswith('rmh2Hdr.xml') or xml_file.endswith('rmh1Hdr.xml'))]
    log.info(f'Processing dir={dir}, files found={len(files)}')
    json_files = []
    for index, chunk in enumerate(file_handler.make_batches(files, batch_size=threads * chunksize * 100)):
        log.info(f'Splitting processing into index file={index}.')
        json_file = f'{file_out}.{index}'
        file_handler.serialize(json_file, file_handler.rmh_2_corpus(chunk, threads=threads, chunksize=chunksize))
        json_files.append(json_file)
    # log.info('Combining files')
    # cat_json(file_out, json_files)
    # log.info('Removing intermediary files')
    # for json_file in json_files:
    #     pathlib.Path(json_file).unlink()
    log.info('Done.')


# https://codereview.stackexchange.com/questions/87254/merging-multiple-json-files-using-python
def cat_json(output_filename, input_filenames):
    def mangle(s):
        return s.strip()[1:-1]

    with open(output_filename, "w+") as outfile:
        first = True
        for infile_name in input_filenames:
            with open(infile_name) as infile:
                if first:
                    outfile.write('[')
                    first = False
                else:
                    outfile.write(',')
                outfile.write(mangle(infile.read()))
        outfile.write(']')


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
cli.add_command(read_rmh)
cli.add_command(deduplicate)


if __name__ == "__main__":
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    cli()
