# Moses model
Eftir að þjálfun á Moses líkani þá er hægt að vista líkanið og dreifa því með Docker.

## Keyrsla
```shell script
docker run -p 8080:8080 haukurp/moses-smt:en-is /opt/moses/bin/moses \
  -threads 4 \
  -f /work/moses.ini \
  --server
# eða
./docker-run.sh
```
Þetta keyrir `moses` forritið með 4 þráðum (til að flýta þýðingum), vísar í skrá þar sem forþjálfað líkan er geymt
og ræsir `moses` sem XMLRPC þýðingarþjón á porti 8080.
Til þess að keyra líkanið á einstökum setningum þar bara að sleppa `--server`.

Fyrir lista af útgefnum forþjálfuðum líkönum sjá [DockerHub](https://hub.docker.com/r/haukurp/moses-smt).

Þjálfaða líkanið gerir ráð fyrir því að fá setningar forunnar á sambærilegan hátt og í þjálfun.
Þess vegna var skrifaður sérstakur [framendi](../frontend/README.md) sem vinnur setningar og 
sendir svo á þjálfað líkan.

## Þróun á líkönum
Öll þróun á líkönum er gerð í gegnum margar bash skipanir, `moses-x.sh`, og yfirleitt keyrt á þjóni sem hefur
aðgang að mörgum kjörnum.
Enn fremur er öll vinnslan hjúpuð með `singularity` og `slurm` í stað `docker` að kröfum margra þjóna.
Sjá `moses-pipeline.sh` fyrir pípu.

## Útgáfa
Keyra scriptu í þessari skrá með nafni á líkani. Sem dæmi: `docker-build.sh en-is-test`.
Þetta mun þýða Moses og ýta myndinni á [DockerHub](https://hub.docker.com/r/haukurp/moses-smt) 
með nafni á líkani sem tagi.
Notandinn þarf að hafa aðgang að DockerHub geymslunni.
Til að skrá sig inn í DockerHub þarf að gera `docker login` fyrst.

Þessi scripta gerir ráð fyrir því að sækja þurfi líkanið á aðra vél.
Breytið eftir þörf.
Hafið þó í huga að í `moses.ini` eru vísanir á skráar staðsetningar sem þarf laga.
