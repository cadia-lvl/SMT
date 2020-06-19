from preprocessing import api


def test_preprocess():
    test = 'Þetta er íslensk setning.'
    result = api.preprocess(test, lang='is')
    print(result)
    assert test != result