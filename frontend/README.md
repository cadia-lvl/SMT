# Moses Frontend
Þessi Python pakki inniheldur:
1. Þýðingarþjón (`server.py`) sem sendir setningar á keyrandi og þjálfað Moses kerfi (XMLRPC).
1. Safn Python falla til þess að forvinna stakar setningar (`core.py`).
1. Safn Python falla til þess að vinna skjöl og nýtir marga þræði (`bulk.py`).
1. Einfaldað viðmót til þess að þýða og forvinna setningar (`api.py`)
1. Python pakka til þess að forvinna stakar setningar og skjöl (setning í línu) fyrir líkanagerð.

```
pip install -e git+https://github.com/cadia-lvl/SMT.git@master#egg=frontend\&subdirectory=frontend
```

Notkun sem skjárhermir.
```shell script
# Forvinna eina íslenska setningu, með útgáfu v2:
frontend preprocess "Þetta er setning." "is" "v2"
```
Dæmi um notkun sem Python safn.
```python
import frontend.api as a
a.preprocess("Þetta er setning.", a.to_lang("is"), "v2")
# 'þetta er setning .\n'
```

## Þýðingarþjónn
```shell script
# Keyra þýðingarþjón í aflúsunarham.
frontend server --debug
```
Athuga hvort þjónn sé keyrandi
```shell script
curl http://127.0.0.1:5000/
# "pong"
```
Þýða setningu:
```shell script
curl -d '{"contents":["A sentence"],"sourceLanguageCode":"en","targetLanguageCode":"is","model":"baseline"}' -H "Content-Type: application/json" http://127.0.0.1:5000/translateText -v
```

## Leyfi
MIT leyfi - sjá `License`.

## Þróun
Gert er ráð fyrir að unnið sé með Conda.
```shell script
conda env create -f environment.yml 
conda activate jupyter
```
- `frontend/api.py` skilgreinir einfalt viðmót fyrir pakkann.
- `frontend/core.py` skilgreinir föll sem taka inn stakar setningar og skilar stökum setningum.
- `frontend/bulk.py` skilgreinir föll sem taka inn skrár og vinnur þær á mörgum þráðum.
- `frontend/server.py` skilgreinir þýðingarþjóninn sem sendir fyrirspurnir á Moses XMLRPC.
- `frontend/cli.py` skilgreinir föllin sem eru aðgengileg í skjáherminum.
- `conftest.py` skilgreinir prófana uppsetningu.
- `setup.py` skilgreinir hvernig á að pakka kóðanum svo hægt sé að nota `pip install`.

Undir `tests/` er ýmsar prófanir. Þegar nýtt fall er útfært skal skrifa prófun fyrir það.
Við nýtum okkur prófunargögn og bendum `pytest` á þau.
```shell script
pytest -s --data=./tests/test_data
```

### Útgáfa
Leiðbeiningar til þess að gefa út nýja útgáfu af `frontend`.
1. Keyra prófanir. Útgefin föll eiga að hafa prófanir og öll próf eiga að fara í gegn.
1. Uppfæra `setup.py` útgáfunúmer.
1. Uppfæra `README.md` með breytingum fyrir útgáfunúmer og leiðbeiningar.
1. Vista breytingar `git commit`.
1. Merkja (`git tag v1.0.2`) kóða með útgáfunúmeri.
1. Ýta breytingum (`git push --tag`).

### Útgáfur
Hér er listi yfir breytingar á milli útgáfa.

#### 2.0.0
Bætt við þýðingarþjón og kóði brotinn í mismunandi skrár.
- `core.py` fyrir staka setninga vinnslu.
- `bulk.py` fyrir skráa vinnslu.
- `server.py` fyrir þýðingarþjón.
- `api.py` fyrir einfalt viðmót á þýðingarvél og forvinnslu.

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
- `known_tok_fraction`. Reiknar hlutfall þekktra orða í setningu.
- `contains_regexp`. Skilar `True` ef setning inniheldur regexp.
- `remove_non_words`. Einfaldar setningu með því að fella út öll orð sem innihalda aðra stafi en bókstafi.
- `corpus_get_skip_lines`. Skilar línum sem ætti að sleppa miðað við þekkt orð og bannaðar regexp.
- `corpus_skip_lines`. Fellir út númer gefinna lína.

#### 1.0.2
`sent_process_v1` breytt til þess að styðja breytt grunnlíkan.

#### 1.0.1
Laga villur frá 1.0.0
