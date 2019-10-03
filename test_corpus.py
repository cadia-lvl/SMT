from typing import List, Set
import pytest

from corpus import ParaCorpus, split_tmx, Corpus, toENISParaCorpus, \
    ENISParaCorpus, combine_corpora, get_filepath, Lang


def test_tmx_split(glob_files):
    tmx_files = glob_files('*.tmx')
    number_of_files = len(tmx_files)
    para_corpora: List[ParaCorpus] = []
    for tmx_file in tmx_files:
        para_corpora.append(split_tmx(tmx_file))
    # Check if the split tmx works.
    assert len(para_corpora) == number_of_files, "We get equally many Para"

    # Check if the datatype is alright.
    all_corpora: Set[Corpus] = set(
        corpus for para_corpus in para_corpora for corpus in para_corpus)
    assert len(all_corpora) == 2*number_of_files, "We get twice as many Corpus"

    # Check if ENISParaCorpus works as intended.
    en_is_para_corpora = [toENISParaCorpus(
        para_corpus) for para_corpus in para_corpora]
    assert len(en_is_para_corpora) == number_of_files
    assert en_is_para_corpora[0].EN.lang == Lang.EN
    assert en_is_para_corpora[0].IS.lang == Lang.IS
    assert en_is_para_corpora[0].EN.lang.value == 'en'
    assert en_is_para_corpora[0].IS.lang.value == 'is'

    # Check if some line counts are ok.
    for corpus in all_corpora:
        if 'baekur' in corpus.filepath:
            assert corpus.get_corpus_info()[2] == 12416
        elif 'tatoeba' in corpus.filepath:
            assert corpus.get_corpus_info()[2] == 8263


def test_load_pipeline(get_pipeline):
    stages = ['baekur',
              'biblian',
              'eso',
              'fornritin',
              'hagstofan',
              'kde4',
              'tatoeba',
              'ubuntu']
    raw_pipeline = get_pipeline(stages)
    # All should be found
    for stage in stages:
        assert isinstance(raw_pipeline[stage], ENISParaCorpus)


def test_combine_corpora(get_pipeline, data_dir):
    stages = ['baekur',
              'biblian',
              'eso',
              'fornritin',
              'hagstofan',
              'kde4',
              'tatoeba',
              'ubuntu']
    raw_pipeline = get_pipeline(stages)

    en_corpora: Set[Corpus] = set(raw_pipeline[stage].EN for stage in stages)
    is_corpora: Set[Corpus] = set(raw_pipeline[stage].IS for stage in stages)

    en_total_length = sum(corpus.get_corpus_info()[2] for corpus in en_corpora)
    is_total_length = sum(corpus.get_corpus_info()[2] for corpus in is_corpora)

    en_target = get_filepath(data_dir, 'cat', Lang.EN)
    en_cat_corpus = combine_corpora(en_corpora, en_target, Lang.EN)
    is_target = get_filepath(data_dir, 'cat', Lang.IS)
    is_cat_corpus = combine_corpora(en_corpora, is_target, Lang.IS)

    assert en_total_length == en_cat_corpus.get_corpus_info()[2]
    assert is_total_length == is_cat_corpus.get_corpus_info()[2]

