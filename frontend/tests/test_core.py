import re

import frontend.core as c
import frontend.definitions as d

def test_regexp():
    # Lets test on a string
    # u'\u0000'-u'\u001f', u'\u007f' - Non-printing characters
    patterns = [{'pattern': re.compile(r"[\u0000-\u001f|\u007f]"), 'repl': 'a'}]
    string = '\u0000a\u001fa\u007fa\u0001a\u007fa'
    output, counter = c.regexp(string, patterns, count=True)
    assert output == 'aaaaaaaaaa'
    assert counter[str(patterns[0]['pattern'])] == 5


def test_specific_regexps():
    test = "En heldur hefði ég kosið, að þessi ráðlegging hefði komið fram fyrr í dag, þannig að ég hefði getað \
nýtt þann tíma, sem farið hefur í það hjá stjórnarliðinu að semja um það, sem hér á að fara fram í dag eða á \
morgun, hátt í 2 klukkutíma í dag, og þá hefði ég vissulega þegið þá ábendingu að kynna mér frekar, hvað hv.\n\
þm.\nSjálfstfl.\nhefðu sagt um ýmis mál hér á undanförnum vikum eða mánuðum. "
    regexps = [
        d.SUB_IS_COMBINE_NEWLINE
    ]
    result, counter = c.regexp(test, regexps, count=True)
    print(test)
    print(result)
    print(counter)
    assert counter[str(regexps[0]['pattern'])] == 2
    assert len(re.findall(r"\n", test)) == 3
    assert len(re.findall(r"\n", result)) == 1


def test_is_tok():
    # Abbreviations
    test = "nr., gr., 1sti fyrsti, 1., 2ja, o.s.frv."
    # Miðeind deep tokenization expands some abbreviations, but inconsistently.
    tokenized = c.tokenize(test, c.Lang.IS, method="pass-through")
    print(tokenized)
    assert tokenized == "númer , grein , fyrsti fyrsti , 1. , tveggja , og svo framvegis ."
    # Miðeind shallow tokenzation understands abbreviations but does not expand.
    tokenized = c.tokenize(test, c.Lang.IS, method="shallow")
    print(tokenized)
    assert tokenized == "nr. , gr. , 1sti fyrsti , 1. , 2ja , o.s.frv ."
    # Moses only understands gr. and o.s.frv. and does not expand.
    tokenized = c.tokenize(test, c.Lang.IS, method='moses')
    print(tokenized)
    assert tokenized == "nr . , gr. , 1sti fyrsti , 1 . , 2ja , o.s.frv."

    # Compounds / Percentages:
    test = "H2O, CO2, 9%"
    # Miðeind tokenizer does not break up compounds and we manually break up percentages.
    tokenized = c.tokenize(test, c.Lang.IS, method="pass-through")
    print(tokenized)
    assert tokenized == "H2O , CO2 , 9 %"
    # Miðeind shallow does not break up compounds and also not percentages.
    tokenized = c.tokenize(test, c.Lang.IS, method="shallow")
    print(tokenized)
    assert tokenized == "H2O , CO2 , 9%"
    # Moses treats compounds correctly and breaks up percentages.
    tokenized = c.tokenize(test, c.Lang.IS, method='moses')
    assert tokenized == "H2O , CO2 , 9 %"
    print(tokenized)

    # URLs:
    test = "http://www.malfong.is"
    # Miðeind deals with URLs
    tokenized = c.tokenize(test, c.Lang.IS, method="pass-through")
    print(tokenized)
    assert tokenized == "http://www.malfong.is"
    # Miðeind shallow also
    tokenized = c.tokenize(test, c.Lang.IS, method="shallow")
    print(tokenized)
    assert tokenized == "http://www.malfong.is"
    # Moses does not
    tokenized = c.tokenize(test, c.Lang.IS, method='moses')
    print(tokenized)
    assert tokenized == "http : / / www.malfong.is"

    # Placeholders:
    test = "ég mun setja _uri_ og _lt_."
    # Miðeind pass-through messes them up and treats them as twitter handles.
    tokenized = c.tokenize(test, c.Lang.IS, method="pass-through")
    print(tokenized)
    assert tokenized == "ég mun setja _ uri _ og _ lt _ ."
    # Miðeind shallow as well.
    tokenized = c.tokenize(test, c.Lang.IS, method="pass-through")
    print(tokenized)
    assert tokenized == "ég mun setja _ uri _ og _ lt _ ."
    # Moses as well.
    tokenized = c.tokenize(test, c.Lang.IS, method='moses')
    print(tokenized)
    assert tokenized == "ég mun setja _ uri _ og _ lt _ ."

    # Sections:
    test = "1.1.1.1.1. Dráttarvélargerð með tilliti til hemlabúnaðar Með \"dráttarvélargerð með tilliti til \
hemlabúnaðar\" er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem:"
    # Miðeind pass-through handles sections (almost) almost correctly. No longer translates " to “
    tokenized = c.tokenize(test, c.Lang.IS, method="pass-through")
    print(tokenized)
    assert tokenized == "1.1.1.1.1 . Dráttarvélargerð með tilliti til hemlabúnaðar Með \" dráttarvélargerð með \
tilliti til hemlabúnaðar \" er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem :"
    # Miðeind shallow does the same.
    tokenized = c.tokenize(test, c.Lang.IS, method="shallow")
    print(tokenized)
    assert tokenized == "1.1.1.1.1 . Dráttarvélargerð með tilliti til hemlabúnaðar Með \" dráttarvélargerð með \
tilliti til hemlabúnaðar \" er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem :"
    # Moses handle sections the same way and does not translate "
    tokenized = c.tokenize(test, c.Lang.IS, method="moses")
    print(tokenized)
    assert tokenized == "1.1.1.1.1 . Dráttarvélargerð með tilliti til hemlabúnaðar Með \" dráttarvélargerð með \
tilliti til hemlabúnaðar \" er átt við dráttarvélar sem eru eins í grundvallaratriðum svo sem :"


def test_fix_incorrect_abbreviations():
    # Error prone sentences:
    tests = ["gr.)? • hvernig er það ákvarðað hvort mengun jarðvegs og grunnvatns „veldur umtalsverðri áhættu fyrir \
heilbrigði manna eða umhverfið“ (3mgr22gr.)?",
             "framkvæmdastjórnin skal einnig birta skýrslu um framvindu framkvæmdarinnar byggða á yfirlitsskýrslum, \
sem aðildarríki leggja fram skv2mgr15gr., og leggja hana fyrir evrópuþingið og aðildarríkin eigi síðar en tveimur \
árum eftir dagsetningarnar sem um getur í 5og 8gr.",
             "hlíti hlutaðeigandi aðildarríki ekki skilyrtum eða neikvæðum ákvörðunum, einkum í tilvikum sem um getur\
 í 14gr., er framkvæmdastjórninni heimilt að vísa málinu beint til dómstóls evrópubandalaganna í \
 samræmi við 2mgr93grsáttmálans.\
enn fremur skal synja um leyfi ef dæmi eru um að upplýsingar eða skjöl, sem fylgja til stuðnings umsókninni, eru ekki í samræmi við ákvæði 8gr., 10gr., 10gra,",
             "í því skyni að ná markmiðunum, sem mælt er fyrir um í 1gr., skal bandalagið grípa til þverlægra aðgerða \
             og ráðstaf- ana til stuðnings sviðsnetum, eins og kveðið er á um í 4til 10grog í samræmi við ida-vinnuáætlunina.",
             "með fyrirvara um þau upplýsingaskipti og notkun upp lýsinga, sem veittar eru skv3mgr5grog 1mgr11gr., skal\
 við málsmeðferð þar sem ekki er farið að tilskildum ákvæðum virða meginreglurnar um trúnaðarkvöð og þagnarskyldu.",
             "greða, í tilviki lánastofnana sem reikna fjárhæðir áhættuveginna áhættuskuldbindinga og vænts \
taps skv83.–89gr., þ au hafa ekki lánshæfismat frá viðurkenndri utanaðkomandi lánshæfismatsstofnun og eru \
metin innanhúss með líkur á vanskilum jafngildar þeim sem tengjast lánshæfismati utanaðkomandi lánshæfismatsstofnunar, \
sem lögbær yfirvöld hafa ákvarðað að sé tengt"
             ]
    regexps = [
        {
            'pattern': re.compile(
                r"(\d+(.\d+)?)(mgr|gr|skv|og|eða|til|með|janúar|febrúar|mars|apríl|maí|júní|júlí|ágúst|september|október|nóvember|desember)"),
            'repl': r"\1. \3"
        },
        {
            'pattern': re.compile(r"(skv)(?=[^.])"),
            'repl': r"\1."
        },
        {
            'pattern': re.compile(r"(\d+(.\d+)?\. )(mgr|gr)(?=[^.])"),
            'repl': r"\1\3. "
        },
    ]
    results = [c.regexp(sent, regexps, count=True) for sent in tests]
    print(results[0])
    assert results[0][1][str(regexps[0]['pattern'])] == 2
    print(results[1])
    assert results[1][1][str(regexps[0]['pattern'])] == 4
    print(results[2])
    assert results[2][1][str(regexps[0]['pattern'])] == 6


def test_en_tok():
    # Abbreviations:
    test = "nr., art., 1st first, 1., 2nd"
    # Moses does not expand abbreviations nor understands them.
    tokenized = c.tokenize(test, c.Lang.EN, 'moses')
    print(tokenized)
    assert tokenized == "nr . , art . , 1st first , 1 . , 2nd"

    # Compounds / Percentages:
    test = "H2O, CO2, 9%"
    # Moses
    tokenized = c.tokenize(test, c.Lang.EN, 'moses')
    print(tokenized)
    assert tokenized == "H2O , CO2 , 9 %"

    # Contractions:
    test = "It's i'm couldn't"
    # Moses also handles contractions, but not in the same way.
    tokenized = c.tokenize(test, c.Lang.EN, 'moses')
    print(tokenized)
    assert tokenized == "It 's i 'm couldn 't"

    # URLs
    test = "http://www.malfong.is"
    # Moses also breaks them up even further
    tokenized = c.tokenize(test, c.Lang.EN, 'moses')
    print(tokenized)
    assert tokenized == "http : / / www.malfong.is"

    # Placeholders
    test = "I will place _uri_ and _lt_."
    # Moses breaks them up
    tokenized = c.tokenize(test, c.Lang.EN, 'moses')
    print(tokenized)
    assert tokenized == "I will place _ uri _ and _ lt _ ."


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
    results = [c.contains_regexp(word, d.CRYLLIC) for word in test]
    assert results == [True, False, False, True, True, False,
                       False, False, True, False]
    results = [c.contains_regexp(word, d.GREEK) for word in test]
    assert results == [False, True, True, False, False, False,
                       False, False, False, False]
    results = [c.contains_regexp(word, d.UNKNOWN_CHARS) for word in test]
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
    print(d.IS_SPLIT_NEWLINE.pattern)
    results = [c.regexp(test, [d.SUB_IS_SPLIT_NEWLINE]) for test in tests]
    for result in results:
        print(result)
    # We test whether our intended transformations happen and some should not.
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
    URI_SUB = {
        'pattern': d.URI,
        'repl': '_uri_'
    }
    URI_SIMPLE_SUB = {
        'pattern': d.URI_SIMPLE,
        'repl': '_uri_'
    }
    for test in tests_uri:
        sub = c.regexp(test, [URI_SUB])
        print(test, sub)
        assert sub == URI_SUB['repl']
    for test in tests_uri_simple:
        sub = c.regexp(test, [URI_SIMPLE_SUB])
        print(test, sub)
        assert sub == URI_SUB['repl']
    for test in tests_uri + tests_uri_simple:
        sub = c.regexp(test, [URI_SUB, URI_SIMPLE_SUB])
        print(test, sub)
        assert sub == URI_SUB['repl']
    for test in tests_uri_not:
        sub = c.regexp(test, [URI_SUB, URI_SIMPLE_SUB])
        print(test, sub)
        assert sub != "_uri_"
