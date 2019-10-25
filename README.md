# Moses þýðingarkerfi
Í þessu skjali er lýst hvernig skal setja upp Moses þýðingarkerfi fyrir frekari þróun.
Einnig er lýst hvernig er hægt að þróa kerfið frekar á Terra-hýsingunni í gegnum Slurm.
Öll þjálfun er gerð í gegnum Jupyter notebooks.

## Keyrsla
Til þess að keyra kerfið þá þarf Docker að vera uppsett.

Keyrsla (þýðing en-is) á einni setningu:
    docker run --rm haukurp/moses-en-is /opt/moses/bin/moses -f moses.ini $(python3 corpus.py --process-sentence "Unpocessed English sentence.")

Keyra Moses þýðingarþjón.
    Vantar

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

Til þess að byggja Docker myndirnar þarf að uppfæra tag (0.1) og vísa í rétta mynd.
Dæmi:
    docker build -t haukurp/moses-smt:0.1 -f moses-Dockerfile .

Til þess að senda myndina á DockerHub þarf aukalega að vera skráður inn í docker `docker login` og hlaða upp ný byggðri mynd.
    docker push haukurp/moses-smt:0.1

## Uppsetning
Leiðbeiningarnar eru unnar úr [opinberum leiðbeiningum Moses](http://www.statmt.org/moses/?n=Development.GetStarted). Sjá þær leiðbeiningar fyrir jaðartilfelli.
Moses kerfið er háð því að önnur forrit séu til staðar í vinnslunni, þeirri uppsetningu er líka lýst.

Best er að byrja á því að sækja þetta repo:

    git clone git@github.com:cadia-lvl/SMT.git 

    mkdir moses
    cd moses
    # EITHER install giza or mgiza. Giza is single threaded, mgiza is multithreaded.
    git clone https://github.com/moses-smt/giza-pp.git
    mkdir -p tools
    ln -s giza-pp/GIZA++-v2/GIZA++ tools/GIZA++
    ln -s giza-pp/GIZA++-v2/snt2cooc.out tools/snt2cooc.out
    ln -s giza-pp/mkcls-v2/mkcls tools/mkcls

    # optional, to run giza multithreaded. Recommended for large corpora.    
    git clone https://github.com/moses-smt/mgiza.git
    mkdir -p tools
    cd mgiza/mgizapp
    cmake .
    make -j4
    make -j4 install
    cp bin/* ../../tools
    cp scripts/merge_alignment.py ../../tools

    # Moses
    git clone git://github.com/moses-smt/mosesdecoder.git
    sudo apt-get install automake \
     libtool \ 
     subversion \ 
     zlib1g-dev \ 
     libboost-all-dev \ 
     libbz2-dev \ 
     liblzma-dev \ 
     python-dev \ 
     grapgviz \ 
     graphviz \ 
     imagemagick \ 
     make \ 
     cmake  \ 
     libgoogle-perftools-dev \
     autoconf \ 
     doxygen

    cd mosesdecoder
    # Þetta forrit er til þess að þjappa saman orðþýingaruppflettingum og hraðar kerfinu töluvert. -j4 notar 4 þræði til að þýða.
    make -j4 -f contrib/Makefiles/install-dependencies.gmake cmph

    ./bjam -j4 --with-cmph=$(pwd)/opt
    cd ..
    
    # Tokenizers and other tools
    git clone --branch patch-1 https://github.com/k4r573n/MosesSuite.git
    cd SMT
    conda env create -f environment.yml 

    # Running the notebook
    # The notebook assumes some environment variables. Examples below
    # You can add the exports to .bashrc if you want.
    export MOSES_SUITE=/home/staff/$USER/moses/MosesSuite
    export MOSESDECODER=/home/staff/$USER/moses/mosesdecoder
    export MOSESDECODER_TOOLS=/home/staff/$USER/moses/tools
    export WORKING_DIR=/mnt/scratch/smt
    export MODEL_DIR=/somewhere
    export THREADS=4

    conda activate jupyter
    jupyter-notebook .

## Keyra prófanir
Það koma nokkrar prófanir (tests) með verkefninu. Þær vinna á prófunar gögnum sem koma ekki með kóðanum. Best er að setja einhver .tmx skjöl í skrá sem heitir 'test_data'. Allar skrárnar sem eru í þeirri skrá eru lesnar og notaðar í prófanir.

Til þess að keyra öll testin:

    pytest

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
    
