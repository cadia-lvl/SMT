# Moses - PBSMT
Moses phrase-based statistical machine translation (Moses PBSMT) er kerfi til þess að þróa og keyra tölfræðilega vélþýðingar.
Í þessu skjali er lýst hvernig hægt er að nota (forþjálfað) Moses þýðingarkerfi og leiðbeiningar fyrir frekari þróun.

Kerfið er gefið út sem nokkrar `Docker` myndir sem hægt er að keyra með `docker` eða `singularity`. Inn í þessum myndum er Moses kerfið uppsett og python forrit til þess að forvinna texta. Gögn fyrir þjálfun er ekki deilt með myndunum (sökum stærðar) en hægt er að nálgast samhliða málheild og einhliðamálheild fyrir íslensku á malfong.is. Fyrir ensku notuðum við USENET einhliða málheildina sem er opin öllum.

Hægt er að keyra forþjálfað kerfi á einstökum setningum í gegnum HTTP (þýðingarþjónn) eða beint.

## Keyrsla
Til þess að keyra kerfið þá þarf `docker` eða `singularity` að vera uppsett.

Keyrsla (þýðing en-is) beint á einni setningu:
    # TODO

Keyra Moses þýðingarþjón.
    # TODO

Keyrsla sem singularity geymir (dæmi)
    singularity run docker://haukurp/moses-lvl:0.1

Keyrsla á Jupyter notebooks í gegnum docker geymi
    docker run -ti -p 8888:8888 -v $PWD:/opt/work haukurp/moses-lvl:0.3 /bin/bash -c "/opt/conda/envs/jupyter/bin/jupyter notebook --notebook-dir=/opt/work --ip='*' --port=8888 --no-browser --allow-root"

## Þróun
Það eru skilgreindar nokkrar Docker myndir í þessu verkefni.

1. `moses-Dockerfile`. Þetta er grunn myndin sem hefur uppsett Moses þýðingarkerfið og önnur tól nauðsynleg til þess að þjálfa og keyra þýðingarkerfið. Þessi mynd er ekki til beinnar notkunar.
1. `corpus-Dockerfile`. Þessi mynd byggir á `moses-Dockerfile` og bætir við Python 3.7 og öðrum python pökkum til þess að forvinna gögn.
1. `en-is-Dockerfile`. Þessi mynd byggir á `corpus-Dockerfile` sem og forþjálfuðu Moses þýðingarkerfi fyrir `en-is` þýðingar.
1. `is-en-Dockerfile`. Alveg eins og `en-is-Dockerfile` nema fyrir `is-en` þýðingar.

Einnig fylgir með Python forrit í skránni `corpus`. Fyrir það verkefni sjá `corpus/README.md`.

Einnig fylgja með nokkur Jupyter vélrit (e. notebook) sem notuð voru við þróun á kerfinu. Til þess að keyra vélritin þá þarf Moses kerfið að vera aðgengilegt. Auðveldast er því að keyra vélritin í gegnum `docker` eða `singularity`, annars þarf að setja kerfisbreyturnar (environment variables) MOSESDECODER og MOSESDECODER_TOOLS og láta þær vísa á skrár sem innihalda nauðsynleg forrit.

Til að keyra vélritin er best að nota (singularity):
    singularity exec -B $PWD:/opt/work docker://haukurp/moses-lvl:0.4 /bin/bash -c "/opt/conda/envs/jupyter/bin/jupyter notebook --notebook-dir=/opt/work --ip='*' --port=8888 --no-browser --allow-root"

### Byggja myndir
Til þess að byggja Docker myndirnar þarf að uppfæra tag (0.1) og vísa í rétta mynd.
Dæmi:
    TAG=0.1
    docker build -t haukurp/moses-smt:$TAG -f moses-Dockerfile .

Til þess að senda myndina á DockerHub þarf aukalega að vera skráður inn í docker `docker login` og hlaða upp ný byggðri mynd.
    docker push haukurp/moses-smt:$TAG

## Keyrsla á Terra cluster (Slurm)
Fyrst þarf að fá aðgang á cluster. Hafðu samband við cluster admin.

- Best er að setja upp Anaconda í home skrá þinni.
- Fylgja leiðbeiningum að ofan um uppsetningu á Moses.

Panta tíma á cluster fyrir jupyter-notebook með 'sbatch' sem er skilgreint í SMT repo.
    
    cd SMT
    sbatch run-jupyter.sbatch

Þetta á að byrja keyrsluna á Juypter notebook. Athugaðu hvort hún keyrir.

    squeue

Þegar hún keyrir, sæktu token-ið til þess að logga inn á notebook.

    grep 'token' -m 1 server.out | awk -F '=' '{print $2}' 

Setja upp SSH tunnel (svo hægt sé að opna þetta á þinni vél). Settu inn notendanafnið þitt á Terra í stað <username>.

    ssh -L 127.0.0.1:8080:127.0.0.1:8080 <username>@terra.hir.is -N
    
