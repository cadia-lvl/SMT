# Corpus
Þetta forrit sér um að forvinna gögn áður en þau eru notuð í líkanagerð.

Í þessu forriti eru mörg stuðningsföll sem vinna beint á texta skrá (og nýta marga þræði) sem og beint á setningar.

Það er hægt að nota forritið beint sem Python safn eða í gengum skjáhermi.
    pip install -e git+https://github.com/cadia-lvl/SMT.git@master#egg=corpus\&subdirectory=corpus 

Fyrir studd föll sjá
    corpus --help

Dæmi um forvinnslu á setningu.
    corpus sent-process-v1 "This is a, super-duper test." "en"
    [nltk_data] Downloading package punkt to /home/haukur/nltk_data...
    [nltk_data]   Package punkt is already up-to-date!
    this is a , super-duper test .

Sami kóð sem Python safn.
    >>> import corpus as c
    >>> c.sent_process_v1("This is a super-duper test.", c.Lang.EN)
    'this is a super-duper test .\n'

Skjáhermis útgáfan styður ekki öll föllin sem eru skilgreind í Python safninu.

## Leyfi
MIT leyfi - sjá `License`.

## Þróun
Gert er ráð fyrir að unnið sé með Conda.
    conda env create -f ../environment.yml #við notum sama environment og er skilgreint fyrir verkefnið í heild sinni.
    conda activate jupyter

- `cli.py` skilgreinir föllin sem eru aðgengileg í skjáherminum.
- `conftest.py` skilgreinir prófana uppsetningu.
- `corpus.py` er kjötið - þ.e. þarna eru öll föllin skilgreind og útfærð til þess að vinna með texta.
- `setup.py` skilgreinir hvernig á að pakka kóðanum svo hægt sé að nota `pip install`.
- `setup.cfg` skilgreinir stillingar fyrir þróun á verkefninu.
- `test_corpus.py` skilgreinir prófanirnar sem eru gerðar á föllum úr `corpus.py`.
- `test_data/*.tmx` í þessa skrá er hægt að setja `.tmx` skjöl til að nota í prófanir.

Keyra prófanir
    pytest -s --data=./test_data

### Útgáfa
Leiðbeiningar til þess að gefa út nýja útgáfu af `corpus`.
1. Keyra prófanir. Útgefin föll eiga að hafa prófanir og öll próf eiga að fara í gegn.
1. Uppfæra `setup.py` útgáfunúmer.
1. Uppfæra `README.md` með breytingum fyrir útgáfunúmer og leiðbeiningar.
1. Vista breytingar `git commit`.
1. Merkja (`git tag v1.0.2`) kóða með útgáfunúmeri.
1. Ýta breytingum (`git push --tag`).

### Útgáfur
Hér er listi yfir breytingar á milli útgáfa.

#### 1.2.0
Ný föll til að auðvelda vinnslu.
- `read(dir, lang, modifiers)` fá `Path` í sérstaka skrá sem er til.
- `write(dir, lang, modifiers)` fá `Path` í sérstaka skrá sem er ekki til.
- `list_dir(dir, lang, modifiers)` fá `List[Path]` í skrár með `modifiers`.
- Prófanir fyrir `Moses` tilreiðara.
- URI leppir betrumbættir.
- `SentencePiece` bætt við í umhverfi.

#### 1.1.1
Villur úr 1.1.0 lagaðar.

#### 1.1.0
Allar regexp settar í safn.
Bætt við föllum.
- `tei_read`. Les `TEI` skjöl og skrifar í eitt skjal.
- `sent_token_known`. Reiknar hlutfall þekktra orða í setningu.
- `sent_contains_regexp`. Skilar `True` ef setning inniheldur regexp.
- `sent_as_words`. Einfaldar setningu með því að fella út öll orð sem innihalda aðra stafi en bókstafi.
- `corpus_get_skip_lines`. Skilar línum sem ætti að sleppa miðað við þekkt orð og bannaðar regexp.
- `corpus_skip_lines`. Fellir út númer gefinna lína.

#### 1.0.2
`sent_process_v1` breytt til þess að styðja breytt grunnlíkan.

#### 1.0.1
Laga villur frá 1.0.0
