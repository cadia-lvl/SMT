# Moses Frontend
Þetta Python verkefni inniheldur:
1. Þýðingarþjón sem sendir setningar á þjálfað Moses kerfi.
1. Safn Python falla til þess að forvinna gögn.

Það er aðgengilegt sem Python safn:
```shell script
pip install git+https://github.com/cadia-lvl/SMT.git@master#egg=frontend\&subdirectory=frontend
```
Eða í gegnum Docker
```shell script
docker run haukurp/moses-lvl:2.0.0
```
### Þýðingarþjónn
```shell script
# Keyra þýðingarþjón í aflúsunarham.
frontend server --debug
# eða
docker run --publish 5000:5000 haukurp/moses-lvl:2.0.0 frontend server --debug
```
Athuga hvort þjónn sé keyrandi
```shell script
curl http://127.0.0.1:5000/
# "pong"
```
Þýða setningu (þetta mun ekki virka nema Moses bakendi er skilgreindur):
```shell script
curl -d '{"contents":["A sentence"],"sourceLanguageCode":"en","targetLanguageCode":"is","model":"baseline"}' -H "Content-Type: application/json" http://127.0.0.1:5000/translateText -v
```
Til að skilgreina Moses bakenda, þ.e. leyfileg `model`s þarf að setja tvær stýrikerfisbreytur:
```shell script
# Skilgreina model "en-is" og vísa á http://localhost:8080/RPC2 og setja preprocessing útgáfu fyrir "en-is" sem "v2".
export MODEL_en_is=http://localhost:8080/RPC2
export PREPROCESSING_en_is=v2
frontend server --debug
# eða
docker run --env PREPROCESSING_en_is=v2 --env MODEL_en_is=http://localhost:8080/RPC2 --publish 5000:5000 haukurp/moses-lvl:2.0.0 frontend server --debug
```

### Forvinnsla gagn
Notkun í skjárhermir.
```shell script
# Forvinna eina íslenska setningu, með útgáfu v2:
frontend preprocess "Þetta er setning." "is" "v2"
# Sjá frontend --help fyrir frekari skipanir.
```

Dæmi um notkun sem Python safn.
```python
import frontend.api as a
a.preprocess("Þetta er setning.", a.to_lang("is"), "v2")
# 'þetta er setning .\n'
```

Fyrir nánari skjölun á pakka sjá `docs/frontend/index.html`.

## Leyfi
MIT leyfi - sjá `LICENSE`.

## Þróun
Gert er ráð fyrir að notandi setji sjálfur upp sýndarumhverfi fyrir Python
```shell script
pip install -r requirements.txt
```

- `frontend/api.py` skilgreinir einfalt viðmót fyrir pakkann.
- `frontend/core.py` skilgreinir föll sem taka inn stakar setningar og skilar stökum setningum.
- `frontend/bulk.py` skilgreinir föll sem taka inn skrár og vinnur þær á mörgum þráðum.
- `frontend/server.py` skilgreinir þýðingarþjóninn sem sendir fyrirspurnir á Moses XMLRPC.
- `frontend/cli.py` skilgreinir föllin sem eru aðgengileg í skjáherminum.
- `conftest.py` skilgreinir prófana uppsetningu.
- `setup.py` skilgreinir hvernig á að pakka kóðanum svo hægt sé að nota `pip install`.
- `requirements.txt` skilgreinir nauðsynleg python söfn til þróunar.

Undir `tests/` er ýmsar prófanir. Þegar nýtt fall er útfært skal skrifa prófun fyrir það.
Við nýtum okkur prófunargögn og bendum `pytest` á þau.
```shell script
pytest -s --data=./tests/test_data
```
- `Dockerfile` skilgreining Docker myndina sem er notuð til þess að dreifa kóðanum.
- `docker-build.sh` er script-a til þess að byggja Docker myndina.

Þegar bætt er við fleiri föllum þarf að bæta við `docstring` fyrir skjölun og svo búa til skjölunina.
```shell script
pdoc --html --force --output-dir docs frontend
```

### Útgáfa
Leiðbeiningar til þess að gefa út nýja útgáfu af `frontend`.
1. Keyra prófanir. Útgefin föll eiga að hafa prófanir og öll próf eiga að fara í gegn.
1. Skilgreina útgáfunúmer: `VERSION=2.0.1`
1. Uppfæra `setup.py` útgáfunúmer.
1. Uppfæra `README.md` með breytingum fyrir útgáfunúmer og leiðbeiningar.
1. Vista breytingar `git commit`.
1. Merkja (`git tag v$VERSION`) kóða með útgáfunúmeri ("v" er bætt fyrir framan útgáfunúmer).
1. Ýta breytingum (`git push --tag`).
1. Byggja og hlaða upp Docker geymi: `bash docker-build.sh $VERSION`

### Útgáfur
Hér er listi yfir breytingar á milli útgáfa.

#### 2.0.6
- Miðeind v2.0.1 tokenizer
- Regexp skilar núna fjölda innsetninga.

#### 2.0.5
- Nokkrar villur lagaðar.
- Bætti við skjölun á Python pakka undir `docs`.
- Miðeind v2.0.0 tokenizer
- Setningavinnsla skilar ekki lengur nýrri línu, char(10), eftir vinnslu.
- "_" notað í stað "@" fyrir leppun þar sem Miðeind Tokenizer skilur @orð sem Twitter notendanafn.

#### 2.0.4
Lagaði úttakið úr þýðingarþjóninum svo þýddar setningar koma út í réttri röð.

#### 2.0.3
Stuðningur fyrir mismunandi model og preprocessing með stýrikerfisbreytum.

#### 2.0.2
Villuleiðréttingar í Flask.

#### 2.0.1
Villuleiðréttingar í nauðsynlegum Python söfnum.

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
