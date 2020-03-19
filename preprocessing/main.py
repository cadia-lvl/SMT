#!/usr/bin/env python
import logging
from glob import glob

import click

from preprocessing import file_handler
from preprocessing import pipeline
from preprocessing.types import (EnrichedPCorpora)
from preprocessing import server as p_server

log = logging.getLogger()


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
@click.argument('lang')
@click.option('--lemma', is_flag=True)
@click.option('--pos', is_flag=True)
@click.option('--form', is_flag=True)
@click.option('--lines', type=int)
@click.option('--threads', type=int, default=1)
@click.option('--chunksize', type=int, default=4000)
def write_factor(input, lang, save_to, lemma, pos, form, lines, threads, chunksize):
    p_corpora: EnrichedPCorpora = file_handler.read_json(input)
    file_handler.write_moses(p_corpora[lang], output_file=save_to, threads=threads, chunksize=chunksize, write_form=form, write_pos=pos, write_lemma=lemma)


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
@click.argument('lang', type=str)
@click.argument('truecase_model', type=str)
def preprocess(input, output, lang, truecase_model):
    output.write("\n".join(pipeline.preprocess(input, lang=lang, truecase_model=truecase_model)))


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
@click.argument('lang', type=str)
def postprocess(input, output, lang):
    output.write("\n".join(pipeline.postprocess(input, lang=lang)))


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('save_to', type=str)
@click.argument('lang', type=str)
@click.option('--threads', type=int, default=1)
def train_truecase(input, save_to, lang, threads):
    """
    Trains Moses truecase model
    """
    log.info(f'save_to={save_to}')
    pipeline.train_truecase(input, save_to=save_to, threads=threads)
    log.info('Done.')


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
@click.argument('load_from')
def truecase(input, output, load_from):
    # The truecaser removes newlines
    for line in pipeline.truecase(input, load_from=load_from):
        output.write(line + '\n')


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
def detruecase(input, output):
    corpus = file_handler.deserialize(input)
    file_handler.serialize(output, (line + '\n' for line in pipeline.detruecase(corpus)))


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w'))
def test(input, output):
    for line in input:
        output.write(line)


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output_train', type=click.File('w+'))
@click.argument('output_test', type=click.File('w+'))
@click.option('--test_size', type=int, default=2000)
@click.option('--shuffle/--no-shuffle', default=True)
@click.option('--seed', type=int, default=42)
def split(input, output_train, output_test, test_size, shuffle, seed):
    corpus = list(file_handler.deserialize(input))
    train, test = pipeline.split(corpus, test_size=test_size, shuffle=shuffle, seed=seed)
    file_handler.serialize(output_train, train)
    file_handler.serialize(output_test, test)
    log.info('Done.')


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
@click.argument('lang')
@click.option('--chunksize', type=int, default=4000, help="Number of lines to process at once.")
@click.option('--lines', type=int, default=0, help="For debugging, limit processing to x lines per corpus. 0 for all.")
def enrich(input, output, lang, chunksize: int, lines: int):
    corpus = file_handler.deserialize(input)
    file_handler.write_json(output, [*pipeline.enrich(corpus, lang=lang, chunksize=chunksize, lines=lines)])
    log.info('Done.')


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
@click.argument('lang')
@click.option('--threads', type=int, default=1)
@click.option('--batch_size', type=int, default=100000)
@click.option('--chunksize', type=int, default=100000)
def tokenize(input, output, lang, threads, batch_size, chunksize):
    log.info('Tokenizing')
    for tokens in pipeline.tokenize(input, lang, threads=threads, batch_size=batch_size, chunksize=chunksize):
        output.write(' '.join(tokens) + '\n')
    log.info('Done.')


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
@click.argument('lang')
def detokenize(input, output, lang):
    corpus = file_handler.deserialize(input)
    file_handler.serialize(output, pipeline.detokenize(corpus, lang))
    log.info('Done.')


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
def deduplicate(input, output):
    known_sent = set()
    log.info('Deduplicating')
    for line in pipeline.deduplicate(input, known=known_sent):
        output.write(line)
    log.info('Done.')


@click.command()
@click.argument('input', type=click.File('r'))
@click.argument('output', type=click.File('w+'))
# TODO: Fix new handling of files
def pickle_to_json(input, output):
    file_handler.write_json(input, file_handler.read_pickle(output))
    log.info('Done.')


@click.command()
@click.argument('dir')
@click.argument('output', type=click.File('w+'))
@click.option('--threads', type=int, default=1, help="Number of threads to use.")
@click.option('--chunksize', type=int, default=400, help="Number of files to process per thread.")
# TODO: Change pipeline so we accept a list of files instead.
def read_rmh(dir, output, threads, chunksize):
    """
    Reads a directory and globs all .xml files (removing hdr files) and extracts all texts. Tailored to RMH .tei format reading.
    Writes the output to .json.
    """
    files = [xml_file for xml_file in glob(f'{dir}/**/*.xml', recursive=True) if not (xml_file.endswith('rmh2Hdr.xml') or xml_file.endswith('rmh1Hdr.xml'))]
    log.info(f'Processing dir={dir}, files found={len(files)}')
    file_handler.serialize(output, (' '.join(line) + '\n' for line in file_handler.rmh_2_corpus(files, threads=threads, chunksize=chunksize)))
    log.info('Done.')


@click.command()
@click.option('--debug', is_flag=True)
def server(debug: bool) -> None:
    p_server.app.run(debug=debug, host='0.0.0.0')


@click.group()
def cli():
    pass


cli.add_command(enrich)
cli.add_command(train_truecase)
cli.add_command(truecase)
cli.add_command(detruecase)
cli.add_command(split)
cli.add_command(write_factor)
cli.add_command(detokenize)
cli.add_command(tokenize)
cli.add_command(read_rmh)
cli.add_command(deduplicate)
cli.add_command(pickle_to_json)
cli.add_command(test)
cli.add_command(preprocess)
cli.add_command(postprocess)
cli.add_command(server)


if __name__ == "__main__":
    import nltk
    # We need to do this somewhere
    nltk.download('wordnet')
    nltk.download('averaged_perceptron_tagger')
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.INFO)
    cli()
