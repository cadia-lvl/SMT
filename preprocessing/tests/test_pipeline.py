from preprocessing import pipeline
from preprocessing import file_handler


def test_truecase():
    truecase_model = './preprocessing/resources/truecase-model.is'
    test = [
        'Þetta er Haukur .',
        'Gunnar á Hlíðarenda .'
    ]
    expected = [
        'þetta er Haukur .',
        'Gunnar á Hlíðarenda .'
    ]
    assert expected == list(pipeline.truecase(corpus=test, load_from=truecase_model))


def test_pre_and_postprocessing():
    test = ['Þetta er setning sem ætti að vera í lÁGSTÖFum. < | [ ] >']
    lang = 'is'
    truecase_model = './preprocessing/resources/truecase-model.is'
    result = list(pipeline.preprocess(test, lang=lang, truecase_model=truecase_model, tokenizer=None, known_tokens=None))[0]
    assert result == 'þetta er setning sem ætti að vera í lágstöfum . _lt_ _pipe_ _bo_ _bc_ _gt_'
    result = list(pipeline.postprocess([result], lang=lang, tokenizer='moses'))[0]
    assert result == 'Þetta er setning sem ætti að vera í lágstöfum. < | [] >'


def test_escape_moses():
    test = '[]<>|'
    result = list(pipeline.escape_moses_chars([test]))
    assert result == ['_bo__bc__lt__gt__pipe_']


def test_deescape_moses():
    test = ['_bo__bc__lt__gt__pipe_']
    result = list(pipeline.de_escape_moses_chars(test))
    assert result == ['[]<>|']


def test_make_batch():
    test = [1, 2, 3]
    batches = []
    for batch in file_handler.make_batches(test, batch_size=1):
        values = list(batch)
        batches.append(values)
    assert batches == [[1], [2], [3]]
    batches = []
    for batch in file_handler.make_batches(test, batch_size=2):
        values = list(batch)
        batches.append(values)
    assert batches == [[1, 2], [3]]
