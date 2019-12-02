import frontend.api as api
import frontend.core as c


# To run these test a server needs to be up and running. See `moses_model/docker-run.sh`
def test_translate_bulk():
    test_sentences = [
        "This is an English sentence, right?",
        "Let's add a few and check the output.",
        "Yes, let's do that."
        "In these cases, smaller bilge wells to cover a reasonable period of time may be permitted.",
        "• hazard classes 3.1 to 3.6, 3.7 adverse effects on sexual function and fertility or on development, 3.8 effects other than narcotic effects, 3.9 and 3.10;",
        "Repeated-dose toxicity studies revealed vacuolation of the tubular cells of the kidneys, with strong evidence for reversibility of the effect.",
        "Concomitant treatment with moderate CYP3A4 inhibitors (e.g., diltiazem, verapamil, clarithromycin, erythromycin, aprepitant, amiodarone) should only be administered with caution in patients receiving 25 mg and should be avoided in patients receiving temsirolimus doses higher than 25 mg.",
        "It should be used with caution in ACS patients:",
        "• Performance,",
        "Dr. Augustine's school?",
        "Marker residue",
        "Lemons",
        "Celeriac",
    ]
    print(api.translate_bulk(test_sentences, c.Lang.EN, 'is-en'))
