import re
from pathlib import Path

import frontend.bulk as b
import frontend.core as c


def test_tmx_split(glob_files):
    tmx_files = [Path(t) for t in glob_files('*.tmx')]
    number_of_files = len(tmx_files)
    result = b.tmx_split(tmx_files, 'EN-GB', 'IS-IS')
    # Check if the split tmx works.
    assert len(result) == number_of_files, "We get equally many Tuples back"

    # Check if the mapping is alright.
    en_corpora, is_corpora = zip(*result)
    assert len(en_corpora) == number_of_files
    assert len(is_corpora) == number_of_files

    assert b.Lang.IS.value == 'is'
    assert b.Lang.EN.value == 'en'

    for corp in en_corpora:
        assert b._lang(corp) == b.Lang.EN
    for corp in is_corpora:
        assert b._lang(corp) == b.Lang.IS

    # Check if some line counts are ok.
    all_corpora = en_corpora + is_corpora
    for corpus in all_corpora:
        if 'tatoeba' in corpus.name:
            assert b.info(corpus)[2] == 8263


def test_load_pipeline(list_data_dir):
    stages = [
        'tatoeba',
        'hagstofan'
    ]
    # All should be found
    for stage in stages:
        raw_pipeline = list_data_dir([b.Lang.IS], stage)
        assert len(raw_pipeline) == 1
        assert isinstance(raw_pipeline[0], Path)
    # Now we test if we can filter
    raw_pipeline = list(filter(
        (lambda path: any([stage in str(path) for stage in stages])),
        list_data_dir([b.Lang.IS])))
    assert len(raw_pipeline) == 2


def test_combine_corpora(list_data_dir, data_dir):
    stages = [
        'tatoeba',
        'hagstofan'
    ]
    is_corpora = list(filter(
        (lambda path: any([stage in str(path) for stage in stages])),
        list_data_dir([b.Lang.IS])))
    en_corpora = list(filter(
        (lambda path: any([stage in str(path) for stage in stages])),
        list_data_dir([b.Lang.EN])))

    en_total_length = sum(b.info(corp)[2] for corp in en_corpora)
    is_total_length = sum(b.info(corp)[2] for corp in is_corpora)

    b.combine(en_corpora, b.write(data_dir, b.Lang.EN, 'cat'))
    b.combine(is_corpora, b.write(data_dir, b.Lang.IS, 'cat'))

    assert en_total_length == b.info(b.read(data_dir, b.Lang.EN, 'cat'))[2]
    assert is_total_length == b.info(b.read(data_dir, b.Lang.IS, 'cat'))[2]
    assert is_total_length == en_total_length


def test_peek_para(data_dir):
    stage = 'cat'
    print(*b.peeks([b.read(data_dir, b.Lang.EN, stage), b.read(data_dir, b.Lang.IS, stage)]))


def same_length_check(path: Path, other_path: Path) -> None:
    assert b.info(path)[2] == b.info(other_path)[2]


def different_check(path: Path, other_path: Path) -> None:
    assert any(line1 != line2 for line1, line2 in
               zip(b.peek(path),
                   b.peek(other_path)))


def test_shuffling(data_dir):
    in_stage = 'cat'
    out_stage = 'shuf'
    p_in = b.read(data_dir, b.Lang.IS, in_stage)
    out = b.write(data_dir, b.Lang.IS, out_stage)
    p_in_2 = b.read(data_dir, b.Lang.EN, in_stage)
    p_out_2 = b.write(data_dir, b.Lang.EN, out_stage)

    # We use the same seed
    b.shuffle(p_in, out, p_in)
    b.shuffle(p_in_2, p_out_2, p_in)

    # Check if at least some of the lines are not the same
    different_check(p_in, out)
    different_check(p_in_2, p_out_2)

    # And that we have the same number of lines
    same_length_check(p_in, out)
    same_length_check(p_in_2, p_out_2)

    # and manually check if the alignment is ok
    print(*b.peeks([out, p_out_2]))


def test_tokenization(data_dir):
    in_stage = 'shuf'
    out_stage = 'tok'
    p_in = b.read(data_dir, b.Lang.IS, in_stage)
    out = b.write(data_dir, b.Lang.IS, out_stage)
    in_2 = b.read(data_dir, b.Lang.EN, in_stage)
    out_2 = b.write(data_dir, b.Lang.EN, out_stage)

    b.tokenize(p_in, out, "shallow")
    b.tokenize(in_2, out_2, 'moses')

    # Check if at least some of the lines are not the same
    different_check(p_in, out)
    different_check(in_2, out_2)

    # And that we have the same number of lines
    same_length_check(p_in, out)
    same_length_check(in_2, out_2)


def test_in_parallel(data_dir):
    in_stage = 'shuf'
    out_stage = 'regexp'
    p_in = b.read(data_dir, b.Lang.IS, in_stage)
    out = b.write(data_dir, b.Lang.IS, out_stage)
    patterns = [(re.compile(r"[\u0000-\u001f|\u007f]"), '')]

    print(b.in_parallel(p_in,
                        out,
                        2,
                        c.regexp,
                        **{"regexps": patterns}))


def test_split(data_dir):
    in_stage = 'shuf'
    out_stage = 'test'
    p_in = b.read(data_dir, b.Lang.IS, in_stage)
    out = b.write(data_dir, b.Lang.IS, out_stage)
    out_stage_2 = 'train'
    out_2 = b.write(data_dir, b.Lang.IS, out_stage_2)

    b.split(p_in, out_2, out, 5000)

    # Check if the combined lengths are equal to the original
    assert b.info(p_in)[2] == b.info(out)[2] + b.info(out_2)[2]

    # And that the test frontend has 5000 lines
    assert b.info(out)[2] == 5000


def test_sample(data_dir):
    in_stage = 'shuf'
    p_in = b.read(data_dir, b.Lang.IS, in_stage)
    sampled_lines = list(b.sample(p_in, 10))
    assert len(sampled_lines) == 10


def test_token_counter(data_dir):
    in_stage = 'shuf'
    p_in = b.read(data_dir, b.Lang.IS, in_stage)
    counter = b.token_counter(p_in)
    # The most common token, this is based on your test data
    assert counter.most_common(1)[0][0] == 'að'


def test_sentence_counter(data_dir):
    in_stage = 'shuf'
    p_in = b.read(data_dir, b.Lang.IS, in_stage)
    counter = b.sentence_counter(p_in)
    # The most common sentence length, this is based on your test data
    assert counter.most_common()[0][0] == 5


def test_tei_read(glob_files):
    tei_files = [Path(t) for t in glob_files('*.xml')]
    out_file = tei_files[0].with_name('rmh.is')
    # we just test if there is no exception
    b.tei_read(tei_files, out_file)


def test_get_drop_lines(data_dir):
    in_stage = 'shuf'
    p_in = b.read(data_dir, b.Lang.IS, in_stage)
    stage = 'shuf'
    # to begin with, we test the edge cases. All should be skipped.
    known_words = set()
    regexps = []
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              1.0,
                              normalize=False,
                              keep_sent_length=0)
    original_length = b.info(p_in)[2]
    assert len(result) == original_length
    # Set the ratio to the bottom, we skip none.
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              0.0,
                              normalize=False,
                              keep_sent_length=0)
    assert len(result) == 0
    # Set the ratio to the bottom and normalize, we skip lines which contain
    # non-word chars (\d\W_).
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              0.0,
                              normalize=True,
                              keep_sent_length=0)
    assert len(result) == 93
    # There are a few one-word sentences
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              1.0,
                              normalize=False)
    assert len(result) == 10369
    # We now normalize. We expect a few more sentences skipped since the
    # sentences which contain only contain non-words are skipped.
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              1.0)
    assert len(result) == 10107
    # We only skip sentences which contain non-word words
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              0.0)
    assert len(result) == 93
    # Increasing above 0 should be equal to 1.0 with no known words
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              0.5)
    assert len(result) == 10107
    # we add a few known words and expect to skip fewer.
    known_words = {"Ég", "skil", "bækurnar", "eftir"}
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              0.5)
    assert len(result) == 9979
    # Adding a regexp we expect to remove more sentences
    known_words = set()
    regexps = [re.compile(r'Ég')]
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              0.5)
    assert len(result) == 10113

    # And now we remove some of the sentences we added with the regexp
    regexps = [re.compile(r'Ég')]
    known_words = {"Ég", "skil", "bækurnar", "eftir"}
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              0.5)
    assert 9979 < len(result) < 10113


def test_drop_lines(data_dir):
    in_stage = 'shuf'
    out_stage = 'skip'
    p_in = b.read(data_dir, b.Lang.IS, in_stage)
    p_out = b.write(data_dir, b.Lang.IS, out_stage)
    regexps = [re.compile(r'Ég')]
    known_words = {"Ég", "skil", "bækurnar", "eftir"}
    result = b.get_drop_lines(p_in,
                              regexps,
                              known_words,
                              0.5)
    assert len(result) == 10112
    lines = [number for number, fraction, line in result]
    b.drop_lines(p_in, p_out, lines)
    assert b.info(p_out)[2] == b.info(p_in)[2] - len(result)
