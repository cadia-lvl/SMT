# Uppsetning á Moses þýðingarkerfi
Í þessu skjali er líst hvernig á að setja upp Moses þýðingarkerfið. Leiðbeiningarnar eru unnar úr [opinberum leiðbeiningum](http://www.statmt.org/moses/?n=Development.GetStarted). Sjá þær leiðbeiningar fyrir jaðartilfelli.

Moses kerfið er háð því að önnur forrit séu til staðar í vinnslunni. Byrjað er að setja þau upp.

Mælt er með að búa til eina skrá sem heitir "moses". Í þessa skrá eru öll forritin uppsett.

    mkdir moses
    cd moses

## Word alignment
Þetta forrit er til þess að setja upp orðfrasaþýðingar.

    git clone https://github.com/moses-smt/giza-pp.git
    mkdir tools
    ln -s giza-pp/GIZA++-v2/GIZA++ tools/GIZA++
    ln -s giza-pp/GIZA++-v2/snt2cooc.out tools/snt2cooc.out
    ln -s giza-pp/mkcls-v2/mkcls tools/mkcls


## Moses

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
    # Þetta forrit er til þess að þjappa saman orðþýingaruppflettingum og hraðar kerfinu töluvert.
    make -f contrib/Makefiles/install-dependencies.gmake cmph

    ./bjam --with-cmph=$(pwd)/opt/local
    cd ..
    
## Tokenizers and other tools

    git clone --branch patch-1 https://github.com/k4r573n/MosesSuite.git
    pip install tokenizer nltk google-cloud-translate

## Running on the Terra cluster
First you need to get access to the cluster. Contact a cluster admin and get a username and password.

- It is recommended to install Anaconda into your home directory on the cluster.
- Install the dependencies from the setup section on the server into your home directory.
    
- clone the project to the server
    
    # assumes that you have an ssh key on the server
    git clone git@github.com:cadia-lvl/SMT.git 

Schedule the jupyter-notebook server using 'sbatch'.

    cd SMT
    sbatch run-jupyter.sbatch

This will schedule the task on the cluster (should take less than 1 second). Check the status by using

    squeue

When the server is running grab the token which you will use to login to the notebook server. 

    grep 'token' -m 1 server.out | awk -F '=' '{print $2}' 

Establish an ssh tunnel to the server running
Subtitude your username into the following command

    ssh -L 127.0.0.1:8080:127.0.0.1:8080 <username>@terra.hir.is -N
    
