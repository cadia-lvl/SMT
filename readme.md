# Moses þýðingarkerfi
Í þessu skjali er lýst hvernig skal setja upp Moses þýðingarkerfi fyrir frekari þróun.
Einnig er lýst hvernig er hægt að þróa kerfið frekar á Terra-hýsingunni í gegnum Slurm.
Öll þjálfun er gerð í gegnum Jupyter notebooks.

## Uppsetning
Leiðbeiningarnar eru unnar úr [opinberum leiðbeiningum](http://www.statmt.org/moses/?n=Development.GetStarted). Sjá þær leiðbeiningar fyrir jaðartilfelli.
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

## Running on the Terra cluster
First you need to get access to the cluster. Contact a cluster admin and get a username and password.

- It is recommended to install Anaconda into your home directory on the cluster.
- Install the dependencies from the setup section on the server into your home directory.
    
Schedule the jupyter-notebook server using 'sbatch' from the SMT repo.

    cd SMT
    sbatch run-jupyter.sbatch

This will schedule the task on the cluster (should take less than 1 second). Check the status by using

    squeue

When the server is running grab the token which you will use to login to the notebook server. 

    grep 'token' -m 1 server.out | awk -F '=' '{print $2}' 

Establish an ssh tunnel to the server running
Subtitude your <username> into the following command

    ssh -L 127.0.0.1:8080:127.0.0.1:8080 <username>@terra.hir.is -N
    
