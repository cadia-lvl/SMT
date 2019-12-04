import api as a
import core as c


def test_process_v1():
    test = "Þetta er íslensk setning, með [ ] () www.mbl.is o.s.frv. <geggjað>!"
    result = a.preprocess(test, c.Lang.IS, "v1")
    print(result)
    assert result == "þetta er íslensk setning , með @uri@ og svo framvegis @lt@ geggjað @gt@ !\n"
    test = "This is an English sentence, with [ ] () www.mbl.is i.e. <awsome>"
    result = a.preprocess(test, c.Lang.EN, "v1")
    print(result)
    assert result == "this is an english sentence , with @uri@ i.e. @lt@awsome@gt@\n"
