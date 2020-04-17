# Pakka Moses líkani
Til þess að pakka Moses líkani þarf að bæta við öllum nauðsynlegum gögnum.
- "Phrase tables"
- "Reordering tables"
- Mállíkani
- Moses stillingum (moses.ini)

Fyrir lista af útgefnum forþjálfuðum líkönum sjá [DockerHub](https://hub.docker.com/r/haukurp/moses-smt).
Þjálfaða líkanið gerir ráð fyrir því að fá setningar forunnar á sambærilegan hátt og í þjálfun.
## Nauðsynlegur hugbúnaður
- Docker
- Skrá inn í DockerHub
- Þjálfað líkan

## `docker-build.sh`
Skriftan sækir skrá með `scp`, byggir docker geymi (eftir `Dockerfile`) og hleður honum upp.
```
./docker-build.sh user@remote.server:/path/on/remote/server docker-image:docker-tag
```

- Skráin verður að innihalda öll nauðsynlegt gögn. Sjá að ofan.
- Skráin `/path/on/remote/server` er sett í skrána `trained_model` og er eytt eftir að líkan hefur verið verið hlaðið upp.

Dæmi:
```
./docker-build.sh haukurpj@torpaq:/work/haukurpj/final-en-is/binarised haukurp/moses-smt:final-en-is
```
## `docker-run.sh`
Skriftan er dæmi um hvernig er hægt að keyra þjálfað líkan.