import frontend.api as a
import frontend.core as c


def test_process_v1():
    test = "Þetta er íslensk setning, með [ ] () www.mbl.is o.s.frv. <geggjað>! 60%"
    result = a.preprocess(test, c.Lang.IS, "v1")
    print(result)
    assert result == "þetta er íslensk setning , með _uri_ og svo framvegis _lt_ geggjað _gt_ ! 60 %"
    test = "This is an English sentence, with [ ] () www.mbl.is i.e. <awsome> 60%"
    result = a.preprocess(test, c.Lang.EN, "v1")
    print(result)
    assert result == "this is an english sentence , with _uri_ i.e. _lt_awsome_gt_ 60 %"


def test_process_v2():
    test = "Þetta er íslensk setning, með [ ] () www.mbl.is o.s.frv. <geggjað>! 60%"
    result = a.preprocess(test, c.Lang.IS, "v2")
    print(result)
    assert result == "þetta er íslensk setning , með _uri_ og svo framvegis _lt_ geggjað _gt_ ! 60 %"
    test = "This is an English sentence, with [ ] () www.mbl.is i.e. <awsome>! 60%"
    result = a.preprocess(test, c.Lang.EN, "v2")
    print(result)
    assert result == "this is an english sentence , with _uri_ i.e. _lt_ awsome ! _gt_ 60 %"


def test_process_v3():
    test = "Þetta er íslensk setning, með [ ] () www.mbl.is o.s.frv. <geggjað>! 60%"
    result = a.preprocess(test, c.Lang.IS, "v3")
    print(result)
    assert result == "þetta er íslensk setning , með _uri_ o.s.frv. _lt_ geggjað _gt_ ! 60%"
    test = "This is an English sentence, with [ ] () www.mbl.is i.e. <awsome>! 60%"
    result = a.preprocess(test, c.Lang.EN, "v3")
    print(result)
    assert result == "this is an english sentence , with _uri_ i.e. _lt_ awsome _gt_ ! 60 %"
