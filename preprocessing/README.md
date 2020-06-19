# Forvinnsla
Hér er Python forrit sem er notað til þess að forvinna gögn áður en Moses líkan er þjálfað sem og til þess að keyra sem þjón til að forvinna gögn fyrir þýðingar.

- `preprocessing` inniheldur Python forritið sem hægt er að nota í skjáhermi til þess að keyra ýmis skref.
- `tests` innihalda nokkrar prófanir á Python forriti.
- `main.py` er notað til þess að keyra Python forritið.
- `requirements.txt` inniheldur lista yfir öll nauðsynleg forrit til þess að keyra Python forritið.
- `Dockerfile` skilgreining Docker myndina sem er notuð til þess að dreifa kóðanum.
- `docker-build.sh` er script-a til þess að byggja Docker myndina.

Python forritið er yfirleitt notað í gengum `scipts` eða sem þjónn.

## Keyrsla
Forvinna texta eða skjal:
```
./main.py preprocess "Íslenskur texti" output.txt "is"
```
Keyrsla á forvinnsluþjóni:
```
./main.py server --debug
```
Til að skilgreina Moses bakenda, þarf að setja stýrikerfisbreytu sem vísar á keyrandi Moses bakenda:
```shell script
export MODEL_en_is_moses=http://moses-en-is:8080/RPC2
```
Fyrir frekari útfærð föll sjá:
```
./main.py --help
```

## Python forrit
- `api.py` skilgreinir einföld föll sem hægt er að kalla í.
- `client.py` skilgreinir föll til þess að senda þýðingarbeiðnir á keyrandi Moses þýðingarvél.
- `file_handler.py` sér um lestur, skrif og aðra hráatexta vinnslu.
- `pipeline.py` skilgreinir föll fyrir einstök skref í textavinnslu.
- `server.py` skilgreinir þjón sem hægt er að keyra til þess að taka á móti þýðingarbeiðnum, forvinna, sendir á Moses og eftirvinnur þýðingar.
- `types.py` útfærir gagna tegundir sem unnið er með í forritinu.