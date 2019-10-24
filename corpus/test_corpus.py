from typing import List, Set
import re
import pytest
from pathlib import Path

import corpus as c


def test_tmx_split(glob_files):
    tmx_files = [Path(t) for t in glob_files('*.tmx')]
    number_of_files = len(tmx_files)
    result = c.tmx_split_(tmx_files, 'EN-GB', 'IS-IS')
    # Check if the split tmx works.
    assert len(result) == number_of_files, "We get equally many Tuples back"

    # Check if the mapping is alright.
    en_corpora, is_corpora = zip(*result)
    assert len(en_corpora) == number_of_files
    assert len(is_corpora) == number_of_files

    assert c.Lang.IS.value == 'is'
    assert c.Lang.EN.value == 'en'

    for corp in en_corpora:
        assert c.corpus_lang(corp) == c.Lang.EN
    for corp in is_corpora:
        assert c.corpus_lang(corp) == c.Lang.IS

    # Check if some line counts are ok.
    all_corpora = en_corpora + is_corpora
    for corpus in all_corpora:
        if 'tatoeba' in corpus.name:
            assert c.corpus_info(corpus)[2] == 8263


def test_load_pipeline(get_pipeline):
    stages = [
        'tatoeba',
        'hagstofan'
    ]
    raw_pipeline = get_pipeline(stages, c.Lang.IS)
    # All should be found
    for stage in stages:
        assert isinstance(raw_pipeline[stage], Path)
    raw_pipeline = get_pipeline(stages, c.Lang.EN)
    # All should be found
    for stage in stages:
        assert isinstance(raw_pipeline[stage], Path)


def test_combine_corpora(get_pipeline):
    stages = [
        'hagstofan',
        'tatoeba'
    ]
    is_corpora = [corpus for name, corpus in get_pipeline(stages,
                                                          c.Lang.IS).items()]
    en_corpora = [corpus for name, corpus in get_pipeline(stages,
                                                          c.Lang.EN).items()]

    en_total_length = sum(c.corpus_info(corp)[2] for corp in en_corpora)
    is_total_length = sum(c.corpus_info(corp)[2] for corp in is_corpora)

    en_cat_corpus = c.corpora_create_path(en_corpora, 'cat')
    c.corpora_combine(en_corpora, en_cat_corpus)

    is_cat_corpus = c.corpora_create_path(is_corpora, 'cat')
    c.corpora_combine(is_corpora, is_cat_corpus)

    assert en_total_length == c.corpus_info(en_cat_corpus)[2]
    assert is_total_length == c.corpus_info(is_cat_corpus)[2]
    assert is_total_length == en_total_length

def test_peek_para_corpus(get_pipeline):
    stages = ['cat']
    is_pipeline = get_pipeline(stages, c.Lang.IS)
    en_pipeline = get_pipeline(stages, c.Lang.EN)
    print(*c.corpora_peek([is_pipeline['cat'], en_pipeline['cat']]))


def test_remove_illegal_chars(get_pipeline):
    stages = ['cat']
    is_pipeline = get_pipeline(stages, c.Lang.IS)
    en_pipeline = get_pipeline(stages, c.Lang.EN)
    # u'\u0000'-u'\u001f', u'\u007f' - Non-printing characters
    patterns = [(re.compile(r"[\u0000-\u001f|\u007f]"), '')]

    # Check that we find some of these characters in the first lines
    assert ord('\u000A') == 10
    assert any(ord(char) == 10 for line in c.corpus_peek(is_pipeline['cat']) for char in line)
    assert any(ord(char) == 10 for line in c.corpus_peek(en_pipeline['cat']) for char in line)
    is_processed_corpus = c.corpus_create_path(is_pipeline['cat'], 'regexp')
    en_processed_corpus = c.corpus_create_path(en_pipeline['cat'], 'regexp')

    c.corpus_regexp(is_pipeline['cat'], is_processed_corpus, patterns)
    c.corpus_regexp(en_pipeline['cat'], en_processed_corpus, patterns)
    # Now all the newlines are gone (atleast from the first lines).
    assert all(ord(char) != 10 for line in c.corpus_peek(is_processed_corpus) for char in line)
    assert all(ord(char) != 10 for line in c.corpus_peek(en_processed_corpus) for char in line)

    # Lets test on a string
    # u'\u0000'-u'\u001f', u'\u007f' - Non-printing characters
    patterns = [(re.compile(r"[\u0000-\u001f|\u007f]"), 'a')]
    string = '\u0000a\u001fa\u007fa\u0001a\u007fa'
    output = c.sent_regexp(string, patterns)
    assert output == 'aaaaaaaaaa'


def same_length_check(path: Path, other_path: Path) -> None:
    assert c.corpus_info(path)[2] == c.corpus_info(other_path)[2]


def corpus_different_check(path: Path, other_path: Path) -> None:
    assert any(line1 != line2 for line1, line2 in
               zip(c.corpus_peek(path),
                   c.corpus_peek(other_path)))


def test_shuffling(get_pipeline):
    stages = ['cat']
    is_pipeline = get_pipeline(stages, c.Lang.IS)
    en_pipeline = get_pipeline(stages, c.Lang.EN)

    is_shuffled_corpus = c.corpus_create_path(is_pipeline['cat'], 'shuf')
    en_shuffled_corpus = c.corpus_create_path(en_pipeline['cat'], 'shuf')
    # We use the same seed
    c.corpus_shuffle(is_pipeline['cat'], is_shuffled_corpus, is_pipeline['cat'])
    c.corpus_shuffle(en_pipeline['cat'], en_shuffled_corpus, is_pipeline['cat'])

    # Check if at least some of the lines are not the same
    corpus_different_check(is_pipeline['cat'],
                           is_shuffled_corpus)
    corpus_different_check(en_pipeline['cat'],
                           en_shuffled_corpus)

    # And that we have the same number of lines
    same_length_check(is_pipeline['cat'],
                      is_shuffled_corpus)
    same_length_check(en_pipeline['cat'],
                      en_shuffled_corpus)

    # and manually check if the alignment is ok
    print(*c.corpora_peek([is_shuffled_corpus, en_shuffled_corpus]))

def test_tokenization_corpus(get_pipeline):
    stages = ['shuf']
    is_pipeline = get_pipeline(stages, c.Lang.IS)
    en_pipeline = get_pipeline(stages, c.Lang.EN)

    is_tok = c.corpus_create_path(is_pipeline['shuf'], 'tok')
    en_tok = c.corpus_create_path(en_pipeline['shuf'], 'tok')

    c.corpus_tokenize(is_pipeline['shuf'], is_tok)
    c.corpus_tokenize(en_pipeline['shuf'], en_tok)

    # We just check if some of the lines have changed
    corpus_different_check(is_pipeline['shuf'],
                           is_tok)
    corpus_different_check(en_pipeline['shuf'],
                           en_tok)


    # And that we have the same number of lines
    same_length_check(is_pipeline['shuf'],
                      is_tok)
    same_length_check(en_pipeline['shuf'],
                      en_tok)

def test_tokenization_sentence():
    test = "nr., gr., 1sti fyrsti, 1., 2ja"
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    assert tokenized == "númer , grein , fyrsti fyrsti , 1. , tveggja"

    test = "H2O, CO2, 9%"
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    # TODO: Pending on Tokenizer patch.
    # assert tokenized == "H2O , CO2 , 9 %"
    print(tokenized)

    # In English we do not expand abbreviations.
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

    # We deal with english contractions
    test = "It's"
    tokenized = c.sent_tokenize(test, c.Lang.EN)
    print(tokenized)
    assert tokenized == "It 's"

    # We deal with URLs
    test = "http://www.malfong.is"
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    print(tokenized)
    assert tokenized == "http://www.malfong.is"
    tokenized = c.sent_tokenize(test, c.Lang.EN)
    print(tokenized)
    # TODO: The NLTK tokenizer does not deal with URLs.
    # assert tokenized == "http://www.malfong.is"

    # How do we deal with lowercases?
    test = "i'm couldn't"
    tokenized = c.sent_tokenize(test, c.Lang.EN)
    print(tokenized)
    assert tokenized == "i 'm could n't"

#
# def test_true_case(get_pipeline):
#     stages = ['tok']
#     pipeline = get_pipeline(stages)
#     truecase_model_is = c.corpus_truecase_train(pipeline['tok'].IS, 'truecase-model')
#     truecase_model_en = c.corpus_truecase_train(pipeline['tok'].EN, 'truecase-model')
#
#     # We just run the truecase
#     truecased_en = c.corpus_truecase_apply(
#         pipeline['tok'].EN, truecase_model_en, 'truecased')
#     truecased_is = c.corpus_truecase_apply(
#         pipeline['tok'].IS, truecase_model_is, 'truecased')
#
#     # We just check if some of the lines have changed
#     corpus_different_check(pipeline[stages[0]].IS,
#                            truecased_is)
#     corpus_different_check(pipeline[stages[0]].EN,
#                            truecased_en)
#
#     # And that we have the same number of lines
#     same_length_check(pipeline[stages[0]].IS,
#                       truecased_is)
#     same_length_check(pipeline[stages[0]].EN,
#                       truecased_en)
#
#     # We test the truecase on specific sentences which we know are in the data.
#     test = 'Það " gunnar "'
#     result = c.sent_truecase(test, truecase_model_is)
#     assert result == 'það " Gunnar "'
#
#     test = 'It " gunnar "'
#     result = c.sent_truecase(test, truecase_model_is)
#     assert result == 'it " Gunnar "'
#
#

def test_corpus_split(get_pipeline):
    stages = ['shuf']
    pipeline = get_pipeline(stages)

    train_is, test_is = c.corpus_split(
        pipeline[stages[0]], ('train', 'test'), 5000)
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


# def test_corpus_sample(get_pipeline):
#     stages = ['truecased']
#     pipeline = get_pipeline(stages)
#     sampled_lines = list(c.corpus_sample(pipeline[stages[0]].IS, 10))
#     assert len(sampled_lines) == 10
#
#
# def test_corpus_token_counter(get_pipeline):
#     stages = ['truecased']
#     pipeline = get_pipeline(stages)
#     counter = c.corpus_token_counter(pipeline[stages[0]].IS)
#     # The most common token is '.'
#     assert counter.most_common(1)[0][0] == '.'
#
#
# def test_corpus_sentence_counter(get_pipeline):
#     stages = ['truecased']
#     pipeline = get_pipeline(stages)
#     counter = c.corpus_sentence_counter(pipeline[stages[0]].IS)
#     # The most common sentence length is 3
#     assert counter.most_common()[0][0] == 3
#
#
# def test_sent_lowercase_normalize():
#     test = "UppEr \u00C7" # LATIN CAPITAL LETTER C WITH CEDILLA
#     test2 = "UppEr \u0043\u0327" # LATIN CAPITAL LETTER C and COMBINING CEDILLA
#     target = "upper \u00E7"
#     assert c.sent_lowercase_normalize(test) == target
#     assert c.sent_lowercase_normalize(test2) == target
