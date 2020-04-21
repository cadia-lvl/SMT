from preprocessing import api


def test_preprocess():
    test = 'Vinnuvélaverkamannaskúrayfirmaður'
    result = api.preprocess(test, lang='is')
    print(result)
    assert test != result