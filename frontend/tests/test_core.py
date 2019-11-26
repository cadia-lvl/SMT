import re

import frontend.core as c


def test_regexp():
    # Lets test on a string
    # u'\u0000'-u'\u001f', u'\u007f' - Non-printing characters
    patterns = [(re.compile(r"[\u0000-\u001f|\u007f]"), 'a')]
    string = '\u0000a\u001fa\u007fa\u0001a\u007fa'
    output = c.regexp(string, patterns)
    assert output == 'aaaaaaaaaa'


def test_specific_regexps():
    test = "En heldur hefði ég kosið, að þessi ráðlegging hefði komið fram fyrr í dag, þannig að ég hefði getað \
nýtt þann tíma, sem farið hefur í það hjá stjórnarliðinu að semja um það, sem hér á að fara fram í dag eða á \
morgun, hátt í 2 klukkutíma í dag, og þá hefði ég vissulega þegið þá ábendingu að kynna mér frekar, hvað hv.\n\
þm.\nSjálfstfl.\nhefðu sagt um ýmis mál hér á undanförnum vikum eða mánuðum. "
    regexps = [
        c.REGEXP_SUB["IS-COMBINE-NEWLINE"]
    ]
    result = c.regexp(test, regexps)
    print(test)
    print(result)
    assert len(re.findall(r"\n", test)) == 3
    assert len(re.findall(r"\n", result)) == 1


def test_is_tok():
    # Miðeind expands some abbreviations
    test = "nr., gr., 1sti fyrsti, 1., 2ja, o.s.frv.\n"
    tokenized = c.tokenize(test, c.Lang.IS)
    assert tokenized == "númer , grein , fyrsti fyrsti , 1. , tveggja , og svo framvegis .\n"

    # Moses only understands gr. and o.s.frv. but does not expand
    tokenized = c.tokenize(test, c.Lang.IS, method='Dockerfile')
    assert tokenized == "nr . , gr. , 1sti fyrsti , 1 . , 2ja , o.s.frv.\n"

    test = "H2O, CO2, 9%\n"
    tokenized = c.tokenize(test, c.Lang.IS)
    # Miðeind tokenizer breaks up H2O to H 2O
    # assert tokenized == "H2O , CO2 , 9 %\n"
    print(tokenized)

    # Moses treats compounds correctly
    tokenized = c.tokenize(test, c.Lang.IS, method='Dockerfile')
    assert tokenized == "H2O , CO2 , 9 %\n"
    print(tokenized)

    # Miðeind deals with URLs
    test = "http://www.malfong.is\n"
    tokenized = c.tokenize(test, c.Lang.IS)
    print(tokenized)
    assert tokenized == "http://www.malfong.is\n"

    # Moses does not
    tokenized = c.tokenize(test, c.Lang.IS, method='Dockerfile')
    print(tokenized)
    assert tokenized == "http : / / www.malfong.is\n"

    # Both will mess-up our placeholders
    test = "ég mun setja @uri@ og @lt@."
    tokenized = c.tokenize(test, c.Lang.IS)
    print(tokenized)
    assert tokenized == "ég mun setja @ uri @ og @ lt @ .\n"

    tokenized = c.tokenize(test, c.Lang.IS, method='Dockerfile')
    print(tokenized)
    assert tokenized == "ég mun setja @ uri @ og @ lt @ .\n"

    # Miðeind handles sections (almost) almost correctly and translates " correctly to “
    test = "1.1.1.1.1. Dráttarvélargerð með tilliti til hemlabúnaðar Með\"dráttarvélargerð með tilliti til \
hemlabúnaðar\"er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem:"
    tokenized = c.tokenize(test, c.Lang.IS, method="pass-through")
    print(tokenized)
    assert tokenized == "1.1.1.1.1 . Dráttarvélargerð með tilliti til hemlabúnaðar Með “ dráttarvélargerð með \
tilliti til hemlabúnaðar “ er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem :\n"
    # Moses handle sections the same way and does not translate "
    tokenized = c.tokenize(test, c.Lang.IS, method="Dockerfile")
    print(tokenized)
    assert tokenized == "1.1.1.1.1 . Dráttarvélargerð með tilliti til hemlabúnaðar Með \" dráttarvélargerð með \
tilliti til hemlabúnaðar \" er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem :\n"


def test_en_tok():
    # In English we do not expand abbreviations.
    test = "nr., art., 1st first, 1., 2nd\n"
    tokenized = c.tokenize(test, c.Lang.EN, 'nltk')
    print(tokenized)
    assert tokenized == "nr. , art. , 1st first , 1. , 2nd\n"
    # Moses does not understand most abbreviations
    tokenized = c.tokenize(test, c.Lang.EN, 'Dockerfile')
    print(tokenized)
    assert tokenized == "nr . , art . , 1st first , 1 . , 2nd\n"
    # TokTok understands better.
    tokenized = c.tokenize(test, c.Lang.EN, 'toktok')
    print(tokenized)
    assert tokenized == "nr. , art. , 1st first , 1. , 2nd\n"

    # TokTok understands compounds, we also know that Moses does.
    test = "H2O, CO2, 9%\n"
    tokenized = c.tokenize(test, c.Lang.EN, 'toktok')
    print(tokenized)
    assert tokenized == "H2O , CO2 , 9 %\n"

    # Each tokenizer deals with contractions differently
    test = "It's i'm couldn't\n"
    tokenized = c.tokenize(test, c.Lang.EN, 'nltk')
    print(tokenized)
    assert tokenized == "It 's i 'm could n't\n"
    tokenized = c.tokenize(test, c.Lang.EN, 'Dockerfile')
    print(tokenized)
    assert tokenized == "It 's i 'm couldn 't\n"
    # TokTok kind-of messes them up
    tokenized = c.tokenize(test, c.Lang.EN, 'toktok')
    print(tokenized)
    assert tokenized == "It ' s i ' m couldn ' t\n"

    test = "http://www.malfong.is\n"
    tokenized = c.tokenize(test, c.Lang.EN, 'nltk')
    print(tokenized)
    # TODO: The NLTK tokenizer does not deal with URLs.
    # assert tokenized == "http://www.malfong.is\n"
    tokenized = c.tokenize(test, c.Lang.EN, 'toktok')
    print(tokenized)
    assert tokenized == "http://www.malfong.is\n"

    # Only TokTok will not mess-up the placeholders
    test = "I will place @uri@ and @lt@."
    tokenized = c.tokenize(test, c.Lang.EN, 'nltk')
    print(tokenized)
    assert tokenized == "I will place @ uri @ and @ lt @ .\n"

    tokenized = c.tokenize(test, c.Lang.EN, method='toktok')
    print(tokenized)
    assert tokenized == "I will place @uri@ and @lt@ .\n"

    tokenized = c.tokenize(test, c.Lang.EN, method='Dockerfile')
    print(tokenized)
    assert tokenized == "I will place @ uri @ and @ lt @ .\n"


def test_lowercase_normalize():
    test = "UppEr \u00C7"  # LATIN CAPITAL LETTER C WITH CEDILLA
    test2 = "UppEr \u0043\u0327"  # LATIN CAPITAL LETTER C and COMBINING CEDILLA
    target = "upper \u00E7"
    assert c.lowercase_normalize(test) == target
    assert c.lowercase_normalize(test2) == target


def test_remove_non_words():
    # all "non-words" should not be present in the sentence.
    test = "these are not words 4.00 3,1415 ? ! - = _ + 1 , : . @ ; ( ) and should be removed"
    result = c.remove_non_words(test)
    assert result == "these are not words and should be removed"


def test_contains_regexp():
    test = ["дейност", "είδοσ", "εγκατάστασησ", "казеин", "приложение", "ž",
            "č", "š", "лицата", "12052"]
    results = [c.contains_regexp(word, c.REGEXP_SUB["CRYLLIC"][0]) for word in test]
    assert results == [True, False, False, True, True, False,
                       False, False, True, False]
    results = [c.contains_regexp(word, c.REGEXP_SUB["GREEK"][0]) for word in test]
    assert results == [False, True, True, False, False, False,
                       False, False, False, False]
    results = [c.contains_regexp(word, c.REGEXP_SUB["UNKNOWN-CHARS"][0]) for word in test]
    assert results == [False, False, False, False, False, True,
                       True, True, False, False]


def test_token_known():
    # First we test whether we count correctly without normalizing.
    test = "these are not words 4.00 3,1415 ? ! - = _ + 1 , : . @ ; ( ) and should be removed"
    result = c.known_tok_fraction(test, {"these", "are", "known", "words", "."})
    test_len = len(test.split())
    known_words_count_in_sent = 4
    assert result == known_words_count_in_sent / test_len
    # Then we test with normalization.
    test = c.remove_non_words(test)
    result = c.known_tok_fraction(test, {"these", "are", "known", "words", "."})
    test_len = 8
    known_words_count_in_sent = 3
    assert result == known_words_count_in_sent / test_len


def test_sentence_breaking():
    # Here are a few sentences from the text which contain "." in weird places.
    # We do not want to cover all these cases, just the most important cases.
    tests = [" viðauka.Skipunarstillipunktar fyrir",
             "test (Method c.32) or",
             "study (Method c.33)c.IV Reproductive",
             "is deleted.Financial liabi",
             "are added.Paragraph 43",
             "A.LIMIT",
             "toxicological a.nd ecotoxicological",
             "The President H.COVENEY",
             "Dental Science (c.Dent.Sc.),",
             "Medicine (Vet.MB or BVet.Med.),",
             "adopted: http://ec.europa.eu/enterprise/reach/docs/ghs/ghs_prop_vol_iii_en.pdf",
             "ul. „V.Levski“ 281",
             "Point XI.C.IX.5 of Annex",
             "IASB at www.iasc.org",
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

    results = [c.regexp(test, [c.REGEXP_SUB["IS-SPLIT-NEWLINE"]]) for test in tests]
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


def test_regexps():
    tests_uri = [
        "www.visir.is",
        "https://circabc.europa.eu/w/browse/d4fbf23d-0da7-47fd-a954-0ada9ca",
        "http://www.mvep.hr/sankcije",
        "www.mbl.is",
        "http://malfong.is",
        "http://www.malfong.is",
        "http://www.malfong.is/",
        "www.garn.is."
    ]
    tests_uri_simple = [
        "visir.is",
    ]
    tests_uri_not = [
        "not.a.uri",
        "o.s.frv."
    ]
    for test in tests_uri:
        print(test, c.regexp(test, [c.REGEXP_SUB["URI"]]))
        assert c.regexp(test, [c.REGEXP_SUB["URI"]]) == "@uri@"
    for test in tests_uri_simple:
        print(test, c.regexp(test, [c.REGEXP_SUB["URI-SIMPLE"]]))
        assert c.regexp(test, [c.REGEXP_SUB["URI-SIMPLE"]]) == "@uri@"
    for test in tests_uri + tests_uri_simple:
        result = c.regexp(test, [c.REGEXP_SUB["URI"], c.REGEXP_SUB["URI-SIMPLE"]])
        print(test, result)
        assert result == "@uri@"
    for test in tests_uri_not:
        print(c.regexp(test, [c.REGEXP_SUB["URI"], c.REGEXP_SUB["URI-SIMPLE"]]))
        assert c.regexp(test, [c.REGEXP_SUB["URI"], c.REGEXP_SUB["URI-SIMPLE"]]) != "@uri@"