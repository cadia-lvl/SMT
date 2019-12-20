import frontend.api as a
import frontend.core as c

test_is = 'Þetta er "íslensk" „setning“ nr. 1.1.1., með H2O www.mbl.is o.s.frv. <geggjað>! 60%'
test_en = 'This is an "English" „sentence“ no. 1.1.1., with H2O www.mbl.is i.e. <awsome>! 60%'


def test_process_v1():
    # Deprecated
    pass
    # result = a.preprocess(test_is, c.Lang.IS, "v1")
    # print(result)
    # assert result == "þetta er \" íslensk \" „ setning “ númer 1.1.1 . , með hæð 2o _uri_ og svo framvegis _lt_ geggjað _gt_ ! 60 %"
    # result = a.preprocess(test_en, c.Lang.EN, "v1")
    # print(result)
    # assert result == "this is an \" english \" „ sentence“ no. 1.1.1. , with h2o _uri_ i.e. _lt_awsome_gt_ ! 60 %"


def test_process_v2():
    result = a.preprocess(test_is, c.Lang.IS, "v2")
    print(result)
    assert result == "þetta er \" íslensk \" „ setning “ númer 1.1.1 . , með hæð 2o _uri_ og svo framvegis _lt_ geggjað _gt_ ! 60 %"
    result = a.preprocess(test_en, c.Lang.EN, "v2")
    print(result)
    assert result == "this is an \" english \" „ sentence “ no . 1.1.1 . , with h2o _uri_ i.e. _lt_ awsome _gt_ ! 60 %"


def test_process_v3():
    result = a.preprocess(test_is, c.Lang.IS, "v3")
    print(result)
    assert result == "þetta er \" íslensk \" „ setning “ nr. 1.1.1 . , með h 2o _uri_ o.s.frv. _lt_ geggjað _gt_ ! 60%"
    result = a.preprocess(test_en, c.Lang.EN, "v3")
    print(result)
    assert result == "this is an \" english \" „ sentence “ no . 1.1.1 . , with h2o _uri_ i.e. _lt_ awsome _gt_ ! 60 %"


def test_postprocess_v3():
    preprocessed = a.preprocess(test_is, c.Lang.IS, "v3")
    print(preprocessed)
    postprocessed = a.postprocess(preprocessed, c.Lang.IS, "v3")
    print(postprocessed)
    assert postprocessed == 'þetta er " íslensk " „setning“ nr. 1.1.1., með h 2o _uri_ o.s.frv. _lt_ geggjað _gt_! 60%'
    preprocessed = a.preprocess(test_en, c.Lang.EN, "v3")
    print(preprocessed)
    postprocessed = a.postprocess(preprocessed, c.Lang.EN, "v3")
    print(postprocessed)
    assert postprocessed == 'this is an "english" „sentence“ no. 1.1.1., with h2o _uri_ i.e. _lt_ awsome _gt_! 60%'

