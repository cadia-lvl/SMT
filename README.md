# Moses - PBSMT
Moses phrase-based statistical machine translation (Moses PBSMT) er 
kerfi til þess að þróa og keyra tölfræðilegar vélþýðingar.
Í þessu skjali er lýst hvernig hægt er að nota (forþjálfað) Moses þýðingarkerfi 
og leiðbeiningar fyrir frekari þróun.

Verkefninu er skipt í nokkra hluta:
1. Moses kerfið uppsett. Dreift með Docker á DockerHub `haukurp/moses-smt:1.1.0`. 
1. Föll til þess að þjálfa og dreifa Moses kerfi.
Forþjálfuðum kerfum er dreift með með Docker á DockerHub `haukurp/moses-smt:en-is` og `haukurp/moses-smt:is-en`.
1. Framendi fyrir þýðingarvél og forvinnsluföll.
Dreift sem Python pakka og Docker á DockerHub `haukurp/moses-lvl:3.2.0`.
1. Aukalega fylgja reiknirit sem eru notuð til þess að forvinna og samhæfa gögn, `preprocessing`, `scripts` og `notebooks`.

# Efnisyfirlit
TODO: Add

# Uppsetning
Þar sem verkefninu er deilt með `docker` þarf einungis að setja upp [`docker`](https://www.docker.com/)

# Keyrsla
Til þess að keyra þýðingu á staka setningu, án þess að setja upp kerfið til lengdar er hægt að gera:
```shell script
echo "Hæ, ég er Moses." | docker run -i haukurp/moses-lvl:3.2.0 ./main.py preprocess - - "is" | docker run -i haukurp/moses-smt:is-en /opt/moses/bin/moses -f /work/moses.ini | docker run -i haukurp/moses-lvl:3.2.0 ./main.py postprocess - - "en" > test
```
Þetta forvinnur setninguna, þýðir hana og lagfærir hana svo og skrifar niðurstöðurnar í skjalið `test`.

Til þess að keyra kerfið í heild sem þýðingarþjón er best að vera með [`docker-compose`](https://docs.docker.com/compose/) uppsett.
```shell script
docker-compose up -d
# Þýða is-en
curl -d '{"contents":["Hæ, ég er Moses."],"sourceLanguageCode":"is","targetLanguageCode":"en","model":"moses"}' -H "Content-Type: application/json" http://localhost:5000/translateText -v
# Þýða en-is
curl -d '{"contents":["Hi, Im Moses"],"sourceLanguageCode":"en","targetLanguageCode":"is","model":"moses"}' -H "Content-Type: application/json" http://localhost:5000/translateText -v
# stöðva
docker-compose down
```

# Leyfi
MIT leyfi [License](LICENSE)

# Höfundar
Háskólinn í Reykjavík

Haukur Páll Jónsson <haukurpj@ru.is>

## Þakkir
Aðrir sem komu að verkefninu eru:
- Hrafn Loftsson (HR)
- Steinþór Steingrímsson (HR/Árnastofnun)
- Haukur Barri Símonarson (Miðeind)
- Vésteinn Snæbjarnarson (Miðeind)

Þetta verkefni var unnið sem hluti af Máltækni áætlun fyrir íslensku 2019-2023. Verkefninu er stýrt af [Almannarómi](https://almannaromur.is/) með styrk frá Menntamálaráðuneytinu.

Kerfið sem er ræst hér er í þremur hlutum sem eru skilgreindir í `docker-compose.yml`.
1. Forþjálfað Moses kerfi fyrir `en-is`
1. Forþjálfað Moses kerfi fyrir `is-en`
1. Framendi sem forvinnur setningar sem koma inn.

# Frekari þróun
Fyrir neðan eru leiðbeiningar fyrir frekari þróun á kerfinu.

## Möppufyrirkomulag
- `data` inniheldur gögn fyrir þjálfun. Sjá nánari lýsingu í [data/README.md](data/README.md).
- `model` inniheldur þjálfun líkön og niðurstöður.
- `moses` inniheldur pökkun og leiðbeiningar fyrir `moses`, kerfið. Sjá nánari lýsingu í [moses/README.md](moses/README.md). Hluti af skjöluninni er á ensku þar sem henni er dreift annars staðar.
- `notebooks` inniheldur rannsóknir á gögnum og er síst vel skjalað.
- `preprocessing` inniheldur Python forrit fyrir forvinnslu þjálfunargagn og framenda. Sjá nánar í [preprocessing/README.md](preprocessing/README.md).
- `scripts` innihalda forvinnslu þjálfunargagna. Sjá nánar í [scripts/README.md](scripts/README.md).

## Gögn
Gögnum fyrir þjálfun er ekki deilt með kerfunum (sökum stærðar) en 
hægt er að nálgast samhliða málheild (is-en) og einmála málheild fyrir íslensku 
á malfong.is.
Sjá frekari leiðbeiningar fyrir gagnafyrirkomulag í [data/README.md](data/README.md)

## Prófanir

### Sjálfvirkar
Það eru skilgreinar nokkrar sjálfvirkarprófanir fyrir Python forrit
```
cd preprocessing
pytest
```

### BLEU stig
en-is þýðingarvél ætti að ná u.þ.b. 48 BLEU stigum
is-en þýðingarvél ætti að ná u.þ.b. 57 BLEU stigum

# Greinar
Ein grein verður gefin út fyrir ráðstefnuna TSD-2020 í tenslum við Moses og íslenskar vélþýðingar. Enn á eftir að gefa hana út.
