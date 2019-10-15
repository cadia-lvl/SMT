from typing import List, Set
import re
import pytest

import corpus as c


def test_tmx_split(glob_files):
    tmx_files = glob_files('*.tmx')
    number_of_files = len(tmx_files)
    para_corpora: List[c.ParaCorpus] = []
    for tmx_file in tmx_files:
        para_corpora.append(c.tmx_split(tmx_file, 'EN-GB', 'IS-IS'))
    # Check if the split tmx works.
    assert len(para_corpora) == number_of_files, "We get equally many Para"

    # Check if the datatype is alright.
    en_corpora: Set[c.Corpus] = set(
        para_corpus.EN for para_corpus in para_corpora)
    is_corpora: Set[c.Corpus] = set(
        para_corpus.IS for para_corpus in para_corpora)
    assert len(en_corpora) == number_of_files
    assert len(is_corpora) == number_of_files

    # Check if ParaCorpus works as intended.
    for para_corpus in para_corpora:
        assert para_corpus.EN.lang == c.Lang.EN
        assert para_corpus.IS.lang == c.Lang.IS
        assert para_corpus.EN.lang.value == 'en'
        assert para_corpus.IS.lang.value == 'is'

    # Check if some line counts are ok.
    all_corpora = en_corpora.union(is_corpora)
    for corpus in all_corpora:
        if 'baekur' in corpus.get_filepath():
            assert corpus.get_corpus_info()[2] == 12416
        elif 'tatoeba' in corpus.get_filepath():
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
        assert isinstance(raw_pipeline[stage], c.ParaCorpus)


def test_combine_corpora(get_pipeline):
    stages = ['baekur',
              'biblian',
              'eso',
              'fornritin',
              'hagstofan',
              'kde4',
              'tatoeba',
              'ubuntu']
    raw_pipeline = get_pipeline(stages)

    en_corpora: Set[c.Corpus] = list(
        raw_pipeline[stage].EN for stage in stages)
    is_corpora: Set[c.Corpus] = list(
        raw_pipeline[stage].IS for stage in stages)

    en_total_length = sum(corpus.get_corpus_info()[2] for corpus in en_corpora)
    is_total_length = sum(corpus.get_corpus_info()[2] for corpus in is_corpora)

    en_cat_corpus = c.corpus_combine(en_corpora, 'cat')
    is_cat_corpus = c.corpus_combine(is_corpora, 'cat')

    assert en_total_length == en_cat_corpus.get_corpus_info()[2]
    assert is_total_length == is_cat_corpus.get_corpus_info()[2]


def test_peek_para_corpus(get_pipeline):
    stages = ['cat']
    pipeline = get_pipeline(stages)
    print(*c.p_corpus_peek(pipeline['cat']))


def test_consolidate_length(get_pipeline):
    stages = ['cat']
    pipeline = get_pipeline(stages)
    assert any(len(line.split(' ')) > 3
               for line in c.corpus_peek(pipeline['cat'].IS))
    assert any(len(line.split(' ')) > 3
               for line in c.corpus_peek(pipeline['cat'].EN))
    consolidated_corpus = c.corpus_length_fix(pipeline['cat'],
                                              'min-1-max-3',
                                              1,
                                              3)
    assert all(len(line.split(' ')) <= 3
               for line in c.corpus_peek(consolidated_corpus.IS))
    assert all(len(line.split(' ')) <= 3
               for line in c.corpus_peek(consolidated_corpus.EN))


def test_remove_illegal_chars(get_pipeline):
    stages = ['cat']
    pipeline = get_pipeline(stages)
    # u'\u0000'-u'\u001f', u'\u007f' - Non-printing characters
    patterns = [(re.compile(r"[\u0000-\u001f|\u007f]"), '')]

    # Check that we find some of these characters in the first lines
    assert ord('\u000A') == 10
    assert any(ord(char) == 10 for line in c.corpus_peek(
        pipeline['cat'].IS) for char in line)
    assert any(ord(char) == 10 for line in c.corpus_peek(
        pipeline['cat'].EN) for char in line)
    processed_corpus = c.ParaCorpus(
        c.corpus_regexp(pipeline['cat'].EN,
                                 'regexp',
                                 patterns),
        c.corpus_regexp(pipeline['cat'].IS,
                                 'regexp',
                                 patterns)
    )
    # Now all the newlines are gone (atleast from the first lines).
    assert all(ord(char) != 10 for line in c.corpus_peek(processed_corpus.IS)
               for char in line)
    assert all(ord(char) != 10 for line in c.corpus_peek(processed_corpus.EN)
               for char in line)

    # Lets test on a string
    # u'\u0000'-u'\u001f', u'\u007f' - Non-printing characters
    patterns = [(re.compile(r"[\u0000-\u001f|\u007f]"), 'a')]
    string = '\u0000a\u001fa\u007fa\u0001a\u007fa'
    output = c.sent_regexp(string, patterns)
    assert output == 'aaaaaaaaaa'


def same_length_check(corpus: c.Corpus, other_corpus: c.Corpus) -> None:
    assert corpus.get_corpus_info()[2] == other_corpus.get_corpus_info()[2]


def corpus_different_check(corpus: c.Corpus, other_corpus: c.Corpus) -> None:
    assert any(line1 != line2 for line1, line2 in
               zip(c.corpus_peek(corpus),
                   c.corpus_peek(other_corpus)))


def test_shuffling(get_pipeline):
    stages = ['min-1-max-3']
    pipeline = get_pipeline(stages)
    # We use the same seed
    shuffled_corpus = c.ParaCorpus(
        c.corpus_shuffle(pipeline[stages[0]].IS,
                         pipeline[stages[0]].IS.get_filepath(),
                         'shuf'),
        c.corpus_shuffle(pipeline[stages[0]].EN,
                         pipeline[stages[0]].IS.get_filepath(),
                         'shuf')
    )

    # Check if at least some of the lines are not the same
    corpus_different_check(pipeline[stages[0]].IS,
                           shuffled_corpus.IS)
    corpus_different_check(pipeline[stages[0]].EN,
                           shuffled_corpus.EN)

    # And that we have the same number of lines
    same_length_check(pipeline[stages[0]].IS,
                      shuffled_corpus.IS)
    same_length_check(pipeline[stages[0]].EN,
                      shuffled_corpus.EN)


def test_tokenization_corpus(get_pipeline):
    stages = ['shuf']
    pipeline = get_pipeline(stages)
    tokenized_corpus = c.ParaCorpus(
        c.corpus_tokenize(pipeline['shuf'].IS, 'tok'),
        c.corpus_tokenize(pipeline['shuf'].EN, 'tok')
    )

    # We just check if some of the lines have changed
    corpus_different_check(pipeline[stages[0]].IS,
                           tokenized_corpus.IS)
    corpus_different_check(pipeline[stages[0]].EN,
                           tokenized_corpus.EN)

    # And that we have the same number of lines
    same_length_check(pipeline[stages[0]].IS,
                      tokenized_corpus.IS)
    same_length_check(pipeline[stages[0]].EN,
                      tokenized_corpus.EN)


def test_tokenization_sentence():
    test = "nr., gr., 1sti fyrsti, 1., 2ja"
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    assert tokenized == "númer , grein , fyrsti fyrsti , 1. , tveggja"

    test = "H2O, CO2, 9%"
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    # TODO: Pending on Tokenizer patch.
    # assert tokenized == "H2O , CO2 , 9 %"
    print(tokenized)

    test = "nr., art., 1st first, 1., 2nd"
    tokenized = c.sent_tokenize(test, c.Lang.EN)
    print(tokenized)
    assert tokenized == "nr. , art. , 1st first , 1. , 2nd"

    test = "Það gunnar"
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    print(tokenized)
    assert tokenized == "Það gunnar"

    test = "H2O, CO2, 9%"
    tokenized = c.sent_tokenize(test, c.Lang.EN)
    print(tokenized)
    assert tokenized == "H2O , CO2 , 9 %"


def test_true_case(get_pipeline):
    stages = ['tok']
    pipeline = get_pipeline(stages)
    truecase_model_is = c.corpus_truecase_train(pipeline['tok'].IS, 'truecase-model')
    truecase_model_en = c.corpus_truecase_train(pipeline['tok'].EN, 'truecase-model')

    # We just run the truecase
    truecased_en = c.corpus_truecase_apply(
        pipeline['tok'].EN, truecase_model_en, 'truecased')
    truecased_is = c.corpus_truecase_apply(
        pipeline['tok'].IS, truecase_model_is, 'truecased')

    # We just check if some of the lines have changed
    corpus_different_check(pipeline[stages[0]].IS,
                           truecased_is)
    corpus_different_check(pipeline[stages[0]].EN,
                           truecased_en)

    # And that we have the same number of lines
    same_length_check(pipeline[stages[0]].IS,
                      truecased_is)
    same_length_check(pipeline[stages[0]].EN,
                      truecased_en)

    # We test the truecase on specific sentences which we know are in the data.
    test = 'Það " gunnar "'
    result = c.sent_truecase(test, truecase_model_is)
    assert result == 'það " Gunnar "'

    test = 'It " gunnar "'
    result = c.sent_truecase(test, truecase_model_is)
    assert result == 'it " Gunnar "'


def test_kenlm(get_pipeline):
    stages = ['truecased']
    pipeline = get_pipeline(stages)
    lm_is = c.kenlm_create(pipeline[stages[0]].IS, 'lm', 3)
    lm_en = c.kenlm_create(pipeline[stages[0]].EN, 'lm', 3)
    print(c.kenlm_eval(lm_is, "þetta er setning"))
    print(c.kenlm_eval(lm_en, "this is a sentence"))


def test_corpus_split(get_pipeline):
    stages = ['truecased']
    pipeline = get_pipeline(stages)

    train_is, test_is = c.corpus_split(
        pipeline[stages[0]].IS, ('train', 'test'), 5000)
    train_en, test_en = c.corpus_split(
        pipeline[stages[0]].EN, ('train', 'test'), 5000)

    # Check if the combined lengths are equal to the original
    assert pipeline[stages[0]].IS.get_corpus_info()[2] == \
        train_is.get_corpus_info()[2] + test_is.get_corpus_info()[2]
    assert pipeline[stages[0]].EN.get_corpus_info()[2] == \
        train_en.get_corpus_info()[2] + test_en.get_corpus_info()[2]

    # And that the test corpus has 5000 lines
    assert test_is.get_corpus_info()[2] == 5000
    assert test_en.get_corpus_info()[2] == 5000


def test_corpus_sample(get_pipeline):
    stages = ['truecased']
    pipeline = get_pipeline(stages)
    sampled_lines = list(c.corpus_sample(pipeline[stages[0]].IS, 10))
    assert len(sampled_lines) == 10
