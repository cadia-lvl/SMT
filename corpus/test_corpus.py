import re
import pytest
from pathlib import Path

import corpus as c


def test_tmx_split(glob_files):
    tmx_files = [Path(t) for t in glob_files('*.tmx')]
    number_of_files = len(tmx_files)
    result = c.tmx_split(tmx_files, 'EN-GB', 'IS-IS')
    # Check if the split tmx works.
    assert len(result) == number_of_files, "We get equally many Tuples back"

    # Check if the mapping is alright.
    en_corpora, is_corpora = zip(*result)
    assert len(en_corpora) == number_of_files
    assert len(is_corpora) == number_of_files

    assert c.Lang.IS.value == 'is'
    assert c.Lang.EN.value == 'en'

    for corp in en_corpora:
        assert c._lang(corp) == c.Lang.EN
    for corp in is_corpora:
        assert c._lang(corp) == c.Lang.IS

    # Check if some line counts are ok.
    all_corpora = en_corpora + is_corpora
    for corpus in all_corpora:
        if 'tatoeba' in corpus.name:
            assert c.corpus_info(corpus)[2] == 8263


def test_load_pipeline(list_data_dir):
    stages = [
        'tatoeba',
        'hagstofan'
    ]
    # All should be found
    for stage in stages:
        raw_pipeline = list_data_dir([c.Lang.IS], stage)
        assert len(raw_pipeline) == 1
        assert isinstance(raw_pipeline[0], Path)
    # Now we test if we can filter
    raw_pipeline = list(filter(
        (lambda path: any([stage in str(path) for stage in stages])),
        list_data_dir([c.Lang.IS])))
    assert len(raw_pipeline) == 2


def test_combine_corpora(list_data_dir, data_dir):
    stages = [
        'tatoeba',
        'hagstofan'
    ]
    is_corpora = list(filter(
        (lambda path: any([stage in str(path) for stage in stages])),
        list_data_dir([c.Lang.IS])))
    en_corpora = list(filter(
        (lambda path: any([stage in str(path) for stage in stages])),
        list_data_dir([c.Lang.EN])))

    en_total_length = sum(c.corpus_info(corp)[2] for corp in en_corpora)
    is_total_length = sum(c.corpus_info(corp)[2] for corp in is_corpora)

    c.combine(en_corpora, c.write(data_dir, c.Lang.EN, 'cat'))
    c.combine(is_corpora, c.write(data_dir, c.Lang.IS, 'cat'))

    assert en_total_length == c.corpus_info(c.read(data_dir, c.Lang.EN, 'cat'))[2]
    assert is_total_length == c.corpus_info(c.read(data_dir, c.Lang.IS, 'cat'))[2]
    assert is_total_length == en_total_length


def test_peek_para_corpus(data_dir):
    stage = 'cat'
    print(*c.corpora_peek([c.read(data_dir, c.Lang.EN, stage), c.read(data_dir, c.Lang.IS, stage)]))


def test_remove_illegal_chars(data_dir):
    in_stage = 'cat'
    out_stage = 'regexp'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    out_corpus = c.write(data_dir, c.Lang.IS, out_stage)
    # u'\u0000'-u'\u001f', u'\u007f' - Non-printing characters
    patterns = [(re.compile(r"[\u0000-\u001f|\u007f]"), '')]

    # Check that we find some of these characters in the first lines
    assert ord('\u000A') == 10
    assert any(ord(char) == 10 for line in c.peek(
        in_corpus) for char in line)

    c.regexp(in_corpus, out_corpus, patterns)
    # Now all the newlines are gone (atleast from the first lines).
    assert all(ord(char) != 10 for line in c.peek(
        out_corpus) for char in line)

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
               zip(c.peek(path),
                   c.peek(other_path)))


def test_shuffling(data_dir):
    in_stage = 'cat'
    out_stage = 'shuf'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    out_corpus = c.write(data_dir, c.Lang.IS, out_stage)
    in_corpus_2 = c.read(data_dir, c.Lang.EN, in_stage)
    out_corpus_2 = c.write(data_dir, c.Lang.EN, out_stage)

    # We use the same seed
    c.shuffle(in_corpus, out_corpus, in_corpus)
    c.shuffle(in_corpus_2, out_corpus_2, in_corpus)

    # Check if at least some of the lines are not the same
    corpus_different_check(in_corpus, out_corpus)
    corpus_different_check(in_corpus_2, out_corpus_2)

    # And that we have the same number of lines
    same_length_check(in_corpus, out_corpus)
    same_length_check(in_corpus_2, out_corpus_2)

    # and manually check if the alignment is ok
    print(*c.corpora_peek([out_corpus, out_corpus_2]))


def test_tokenization_corpus(data_dir):
    in_stage = 'shuf'
    out_stage = 'tok'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    out_corpus = c.write(data_dir, c.Lang.IS, out_stage)
    in_corpus_2 = c.read(data_dir, c.Lang.EN, in_stage)
    out_corpus_2 = c.write(data_dir, c.Lang.EN, out_stage)

    c.tokenize(in_corpus, out_corpus)
    c.tokenize(in_corpus_2, out_corpus_2, 'nltk')

    # Check if at least some of the lines are not the same
    corpus_different_check(in_corpus, out_corpus)
    corpus_different_check(in_corpus_2, out_corpus_2)

    # And that we have the same number of lines
    same_length_check(in_corpus, out_corpus)
    same_length_check(in_corpus_2, out_corpus_2)


def test_specific_regexps():
    test = "En heldur hefði ég kosið, að þessi ráðlegging hefði komið fram fyrr í dag, þannig að ég hefði getað \
nýtt þann tíma, sem farið hefur í það hjá stjórnarliðinu að semja um það, sem hér á að fara fram í dag eða á \
morgun, hátt í 2 klukkutíma í dag, og þá hefði ég vissulega þegið þá ábendingu að kynna mér frekar, hvað hv.\n\
þm.\nSjálfstfl.\nhefðu sagt um ýmis mál hér á undanförnum vikum eða mánuðum. "
    regexps = [
        c.REGEXP_SUB["IS-COMBINE-NEWLINE"]
    ]
    result = c.sent_regexp(test, regexps)
    print(test)
    print(result)
    assert len(re.findall(r"\n", test)) == 3
    assert len(re.findall(r"\n", result)) == 1


def test_is_sent_tok():
    # Miðeind expands some abbreviations
    test = "nr., gr., 1sti fyrsti, 1., 2ja, o.s.frv.\n"
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    assert tokenized == "númer , grein , fyrsti fyrsti , 1. , tveggja , og svo framvegis .\n"

    # Moses only understands gr. and o.s.frv. but does not expand
    tokenized = c.sent_tokenize(test, c.Lang.IS, method='moses')
    assert tokenized == "nr . , gr. , 1sti fyrsti , 1 . , 2ja , o.s.frv.\n"

    test = "H2O, CO2, 9%\n"
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    # Miðeind tokenizer breaks up H2O to H 2O
    # assert tokenized == "H2O , CO2 , 9 %\n"
    print(tokenized)

    # Moses treats compounds correctly
    tokenized = c.sent_tokenize(test, c.Lang.IS, method='moses')
    assert tokenized == "H2O , CO2 , 9 %\n"
    print(tokenized)

    # Miðeind deals with URLs
    test = "http://www.malfong.is\n"
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    print(tokenized)
    assert tokenized == "http://www.malfong.is\n"

    # Moses does not
    tokenized = c.sent_tokenize(test, c.Lang.IS, method='moses')
    print(tokenized)
    assert tokenized == "http : / / www.malfong.is\n"

    # Both will mess-up our placeholders
    test = "ég mun setja @uri@ og @lt@."
    tokenized = c.sent_tokenize(test, c.Lang.IS)
    print(tokenized)
    assert tokenized == "ég mun setja @ uri @ og @ lt @ .\n"

    tokenized = c.sent_tokenize(test, c.Lang.IS, method='moses')
    print(tokenized)
    assert tokenized == "ég mun setja @ uri @ og @ lt @ .\n"

    # Miðeind handles sections (almost) almost correctly and translates " correctly to “
    test = "1.1.1.1.1. Dráttarvélargerð með tilliti til hemlabúnaðar Með\"dráttarvélargerð með tilliti til \
hemlabúnaðar\"er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem:"
    tokenized = c.sent_tokenize(test, c.Lang.IS, method="pass-through")
    print(tokenized)
    assert tokenized == "1.1.1.1.1 . Dráttarvélargerð með tilliti til hemlabúnaðar Með “ dráttarvélargerð með \
tilliti til hemlabúnaðar “ er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem :\n"
    # Moses handle sections the same way and does not translate "
    tokenized = c.sent_tokenize(test, c.Lang.IS, method="moses")
    print(tokenized)
    assert tokenized == "1.1.1.1.1 . Dráttarvélargerð með tilliti til hemlabúnaðar Með \" dráttarvélargerð með \
tilliti til hemlabúnaðar \" er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem :\n"


def test_en_sent_tok():
    # In English we do not expand abbreviations.
    test = "nr., art., 1st first, 1., 2nd\n"
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'nltk')
    print(tokenized)
    assert tokenized == "nr. , art. , 1st first , 1. , 2nd\n"
    # Moses does not understand most abbreviations
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'moses')
    print(tokenized)
    assert tokenized == "nr . , art . , 1st first , 1 . , 2nd\n"
    # TokTok understands better.
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'toktok')
    print(tokenized)
    assert tokenized == "nr. , art. , 1st first , 1. , 2nd\n"

    # TokTok understands compounds, we also know that Moses does.
    test = "H2O, CO2, 9%\n"
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'toktok')
    print(tokenized)
    assert tokenized == "H2O , CO2 , 9 %\n"

    # Each tokenizer deals with contractions differently
    test = "It's i'm couldn't\n"
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'nltk')
    print(tokenized)
    assert tokenized == "It 's i 'm could n't\n"
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'moses')
    print(tokenized)
    assert tokenized == "It 's i 'm couldn 't\n"
    # TokTok kind-of messes them up
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'toktok')
    print(tokenized)
    assert tokenized == "It ' s i ' m couldn ' t\n"

    test = "http://www.malfong.is\n"
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'nltk')
    print(tokenized)
    # TODO: The NLTK tokenizer does not deal with URLs.
    # assert tokenized == "http://www.malfong.is\n"
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'toktok')
    print(tokenized)
    assert tokenized == "http://www.malfong.is\n"

    # Only TokTok will not mess-up the placeholders
    test = "I will place @uri@ and @lt@."
    tokenized = c.sent_tokenize(test, c.Lang.EN, 'nltk')
    print(tokenized)
    assert tokenized == "I will place @ uri @ and @ lt @ .\n"

    tokenized = c.sent_tokenize(test, c.Lang.EN, method='toktok')
    print(tokenized)
    assert tokenized == "I will place @uri@ and @lt@ .\n"

    tokenized = c.sent_tokenize(test, c.Lang.EN, method='moses')
    print(tokenized)
    assert tokenized == "I will place @ uri @ and @ lt @ .\n"


def test_in_parallel(data_dir):
    in_stage = 'shuf'
    out_stage = 'regexp'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    out_corpus = c.write(data_dir, c.Lang.IS, out_stage)
    patterns = [(re.compile(r"[\u0000-\u001f|\u007f]"), '')]

    c.in_parallel(in_corpus,
                  out_corpus,
                  2,
                  c.sent_regexp,
                  **{"regexps": patterns})


def test_corpus_split(data_dir):
    in_stage = 'shuf'
    out_stage = 'test'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    out_corpus = c.write(data_dir, c.Lang.IS, out_stage)
    out_stage_2 = 'train'
    out_corpus_2 = c.write(data_dir, c.Lang.IS, out_stage_2)

    c.split(in_corpus, out_corpus_2, out_corpus, 5000)

    # Check if the combined lengths are equal to the original
    assert c.corpus_info(in_corpus)[2] == c.corpus_info(out_corpus)[2] + c.corpus_info(out_corpus_2)[2]

    # And that the test corpus has 5000 lines
    assert c.corpus_info(out_corpus)[2] == 5000


def test_corpus_sample(data_dir):
    in_stage = 'shuf'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    sampled_lines = list(c.sample(in_corpus, 10))
    assert len(sampled_lines) == 10


def test_corpus_token_counter(data_dir):
    in_stage = 'shuf'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    counter = c.token_counter(in_corpus)
    # The most common token, this is based on your test data
    assert counter.most_common(1)[0][0] == 'að'


def test_corpus_sentence_counter(data_dir):
    in_stage = 'shuf'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    counter = c.sentence_counter(in_corpus)
    # The most common sentence length, this is based on your test data
    assert counter.most_common()[0][0] == 5


def test_sent_lowercase_normalize():
    test = "UppEr \u00C7"  # LATIN CAPITAL LETTER C WITH CEDILLA
    test2 = "UppEr \u0043\u0327"  # LATIN CAPITAL LETTER C and COMBINING CEDILLA
    target = "upper \u00E7"
    assert c.sent_lowercase_normalize(test) == target
    assert c.sent_lowercase_normalize(test2) == target


def test_sentence_breaking():
    # Here are a few sentences from the text which contain "." in weird places.
    # We do not want to cover all these cases, just the most important cases.
    tests = [" viðauka.Skipunarstillipunktar fyrir",
             "test (Method B.32) or",
             "study (Method B.33)B.IV Reproductive",
             "is deleted.Financial liabi",
             "are added.Paragraph 43",
             "A.LIMIT",
             "toxicological a.nd ecotoxicological",
             "The President H.COVENEY",
             "Dental Science (B.Dent.Sc.),",
             "Medicine (Vet.MB or BVet.Med.),",
             "adopted: http://ec.europa.eu/enterprise/reach/docs/ghs/ghs_prop_vol_iii_en.pdf",
             "ul. „V.Levski“ 281",
             "Point XI.C.IX.5 of Annex",
             "IASB at www.iasb.org",
             "Te.st conditions",
             " o.s.frv. sem starfa",
             "„3a.GERÐARVIÐURKENNING",
             "er minna en 15.Hægt er",
             "i.efni sem uppfyllir",
             "III.VIÐAUKI",
             "skulu a.m.kkveða á um að",
             "(Stjtíð.EB L",
             "(4).Til",
             "2.2.3.4.Meginregla ",
             "ammóníakslausn (3.2.ii)) og",
             "framkvæmdastjórnarinnar (EB) nr.416/2005 (Stjtíð.ESB L 66, 12.3.2005, bls. 10).",
             "lýkur 31.mars 2006",
             "asdf.Þ"
             ]

    results = [c.sent_regexp(test, [c.REGEXP_SUB["IS-SPLIT-NEWLINE"]]) for test in tests]
    for result in results:
        print(result)
    # We test wether our intended transformations happen and some should not.
    assert " viðauka. Skipunarstillipunktar fyrir" in results
    assert "is deleted. Financial liabi" in results
    assert "are added. Paragraph 43" in results
    assert "„3a. GERÐARVIÐURKENNING" in results
    assert "er minna en 15. Hægt er" in results
    assert "(4). Til" in results
    assert "2.2.3.4. Meginregla " in results
    assert "asdf. Þ" in results
    assert "adopted: http://ec.europa.eu/enterprise/reach/docs/ghs/ghs_prop_vol_iii_en.pdf" in results
    assert " o.s.frv. sem starfa" in results


def test_sent_process_v1():
    test = "Þetta er íslensk setning, með [ ] () www.mbl.is o.s.frv. <geggjað>!"
    result = c.sent_process_v1(test, c.Lang.IS)
    print(result)
    assert result == "þetta er íslensk setning , með @uri@ og svo framvegis @lt@ geggjað @gt@ !\n"
    test = "This is an English sentence, with [ ] () www.mbl.is i.e. <awsome>"
    result = c.sent_process_v1(test, c.Lang.EN)
    print(result)
    assert result == "this is an english sentence , with @uri@ i.e. @lt@awsome@gt@\n"


def test_tei_read(glob_files):
    tei_files = [Path(t) for t in glob_files('*.xml')]
    out_file = tei_files[0].with_name('rmh.is')
    # we just test if there is no exception
    c.tei_read(tei_files, out_file)


def test_sent_as_words():
    # all "non-words" should not be present in the sentence.
    test = "these are not words 4.00 3,1415 ? ! - = _ + 1 , : . @ ; ( ) and should be removed"
    result = c.sent_as_words(test)
    assert result == "these are not words and should be removed"


def test_sent_contains_regexp():
    test = ["дейност", "είδοσ", "εγκατάστασησ", "казеин", "приложение", "ž",
            "č", "š", "лицата", "12052"]
    results = [c.sent_contains_regexp(word, c.REGEXP_SUB["CRYLLIC"][0]) for word in test]
    assert results == [True, False, False, True, True, False,
                       False, False, True, False]
    results = [c.sent_contains_regexp(word, c.REGEXP_SUB["GREEK"][0]) for word in test]
    assert results == [False, True, True, False, False, False,
                       False, False, False, False]
    results = [c.sent_contains_regexp(word, c.REGEXP_SUB["UNKNOWN-CHARS"][0]) for word in test]
    assert results == [False, False, False, False, False, True,
                       True, True, False, False]


def test_sent_token_known():
    # First we test whether we count correctly without normalizing.
    test = "these are not words 4.00 3,1415 ? ! - = _ + 1 , : . @ ; ( ) and should be removed"
    result = c.sent_token_known(test, set(["these", "are", "known", "words", "."]))
    test_len = len(test.split())
    known_words_count_in_sent = 4
    assert result == known_words_count_in_sent / test_len
    # Then we test with normalization.
    test = c.sent_as_words(test)
    result = c.sent_token_known(test, set(["these", "are", "known", "words", "."]))
    test_len = 8
    known_words_count_in_sent = 3
    assert result == known_words_count_in_sent / test_len


def test_corpus_get_skip_lines(data_dir):
    in_stage = 'shuf'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    stage = 'shuf'
    # to begin with, we test the edge cases. All should be skipped.
    known_words = set()
    regexps = []
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              1.0,
                              normalize=False,
                              keep_sent_length=0)
    original_length = c.corpus_info(in_corpus)[2]
    assert len(result) == original_length
    # Set the ratio to the bottom, we skip none.
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              0.0,
                              normalize=False,
                              keep_sent_length=0)
    assert len(result) == 0
    # Set the ratio to the bottom and normalize, we skip lines which contain
    # non-word chars (\d\W_).
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              0.0,
                              normalize=True,
                              keep_sent_length=0)
    assert len(result) == 93
    # There are a few one-word sentences
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              1.0,
                              normalize=False)
    assert len(result) == 10369
    # We now normalize. We expect a few more sentences skipped since the
    # sentences which contain only contain non-words are skipped.
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              1.0)
    assert len(result) == 10107
    # We only skip sentences which contain non-word words 
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              0.0)
    assert len(result) == 93
    # Increasing above 0 should be equal to 1.0 with no known words
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              0.5)
    assert len(result) == 10107
    # we add a few known words and expect to skip fewer.
    known_words = {"Ég", "skil", "bækurnar", "eftir"}
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              0.5)
    assert len(result) == 9979
    # Adding a regexp we expect to remove more sentences
    known_words = set()
    regexps = [re.compile(r'Ég')]
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              0.5)
    assert len(result) == 10113

    # And now we remove some of the sentences we added with the regexp
    regexps = [re.compile(r'Ég')]
    known_words = {"Ég", "skil", "bækurnar", "eftir"}
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              0.5)
    assert len(result) > 9979 and len(result) < 10113


def test_corpus_skip_lines(data_dir):
    in_stage = 'shuf'
    out_stage = 'skip'
    in_corpus = c.read(data_dir, c.Lang.IS, in_stage)
    out_corpus = c.write(data_dir, c.Lang.IS, out_stage)
    regexps = [re.compile(r'Ég')]
    known_words = {"Ég", "skil", "bækurnar", "eftir"}
    result = c.get_skip_lines(in_corpus,
                              regexps,
                              known_words,
                              0.5)
    assert len(result) == 10112
    lines = [number for number, fraction, line in result]
    c.skip_lines(in_corpus, out_corpus, lines)
    assert c.corpus_info(out_corpus)[2] == c.corpus_info(in_corpus)[2] - len(result)


def test_regexps():
    tests_uri = [
        "www.visir.is",
        "https://circabc.europa.eu/w/browse/d4fbf23d-0da7-47fd-a954-0ada9ca",
        "http://www.mvep.hr/sankcije",
        "www.mbl.is",
        "http://malfong.is",
        "http://www.malfong.is"
        "http://www.malfong.is/"
    ]
    tests_uri_simple = [
        "visir.is",
    ]
    tests_uri_not = [
        "not.a.uri",
        "o.s.frv."
    ]
    for test in tests_uri:
        print(c.sent_regexp(test, [c.REGEXP_SUB["URI"]]))
        assert c.sent_regexp(test, [c.REGEXP_SUB["URI"]]) == "@uri@"
    for test in tests_uri_simple:
        print(c.sent_regexp(test, [c.REGEXP_SUB["URI-SIMPLE"]]))
        assert c.sent_regexp(test, [c.REGEXP_SUB["URI-SIMPLE"]]) == "@uri@"
    for test in tests_uri_not:
        print(c.sent_regexp(test, [c.REGEXP_SUB["URI"], c.REGEXP_SUB["URI-SIMPLE"]]))
        assert c.sent_regexp(test, [c.REGEXP_SUB["URI"], c.REGEXP_SUB["URI-SIMPLE"]]) != "@uri@"
