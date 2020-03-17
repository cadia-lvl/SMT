from preprocessing import pipeline


def test_truecase():
    truecase_model = '/work/haukurpj/data/mideind/truecase-model.form.is'
    test = [
        ['Þetta', 'er', 'Haukur', '.'],
        ['Gunnar', 'á', 'Hlíðarenda', '.']
    ]
    expected = [
        ['þetta', 'er', 'haukur', '.'],
        ['Gunnar', 'á', 'Hlíðarenda', '.']
    ]
    assert expected == pipeline.truecase(corpus=test, load_from=truecase_model)


def test_enriched_corpus_truecase():
    truecase_model_form = '/work/haukurpj/data/mideind/truecase-model.form.is'
    truecase_model_lemma = '/work/haukurpj/data/mideind/truecase-model.lemma.is'
    test = [
        (['Þetta', 'er', 'Haukur', '.'], ['1', '2', '3', '4'], ['þessi', 'vera', 'Haukur', '.']),
        (['Gunnar', 'á', 'Hlíðarenda', '.'], ['1', '2', '3', '4'], ['Gunnar', 'á', 'Hlíðarendi', '.'])
    ]
    expected_form = [
        (['þetta', 'er', 'haukur', '.'], ['1', '2', '3', '4'], ['þessi', 'vera', 'Haukur', '.']),
        (['Gunnar', 'á', 'Hlíðarenda', '.'], ['1', '2', '3', '4'], ['Gunnar', 'á', 'Hlíðarendi', '.'])
    ]
    expected_lemma = [
        (['Þetta', 'er', 'Haukur', '.'], ['1', '2', '3', '4'], ['þessi', 'vera', 'Haukur', '.']),
        (['Gunnar', 'á', 'Hlíðarenda', '.'], ['1', '2', '3', '4'], ['Gunnar', 'á', 'Hlíðarendi', '.'])
    ]
    assert expected_form == pipeline.truecase_enriched_corpus(corpus=test, load_from=truecase_model_form, segment='form')
    assert expected_lemma == pipeline.truecase_enriched_corpus(corpus=test, load_from=truecase_model_lemma, segment='lemma')


def test_preprocessing():
    test = ['Þetta er setning sem ætti að vera í lÁGSTÖFum. < |']
    lang = 'is'
    result = pipeline.preprocess(test, lang=lang, truecase_model='/work/haukurpj/data/train/truecase-model.form.en')
    assert result == ['þetta er setning sem ætti að vera í lágstöfum . _lt_ _pipe_'] 
