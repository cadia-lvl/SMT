# Moses SMT
This image is based on previous work: https://github.com/amake/moses-smt

The image is built from ubuntu:18.04 and installs the Moses SMT system to `MOSESDECODER=/opt/moses`
 with multithreaded GIZA++ `mgiza` to `MOSESDECODER_TOOLS=/opt/moses_tools`.
 Additionally python 2.7 is installed for `merge_alignment.py`.
 All dependencies are built. 
- `xmlrpc` the Moses XMLRPC server.
- `cmph` enables binarization/packaging of a trained Moses system.
- `boost` is a collection of C++ libraries.

## Usage
This image can be used instead of installing Moses on a local computer.
The interaction with the docker container behaves in the same way as an installed Moses.
 That is, the commands are called the same and take the same arguments.
 No adjustments were done on the compiled code.

For example, working from [the baseline model](http://www.statmt.org/moses/?n=Moses.Baseline) on the Moses site, we download and extract the example data to `$HOME/corpus` on the local machine and instead of executing the tokenization step as:
```
~/mosesdecoder/scripts/tokenizer/tokenizer.perl -l en \
    < ~/corpus/training/news-commentary-v8.fr-en.en    \
    > ~/corpus/news-commentary-v8.fr-en.tok.en
~/mosesdecoder/scripts/tokenizer/tokenizer.perl -l fr \
    < ~/corpus/training/news-commentary-v8.fr-en.fr    \
    > ~/corpus/news-commentary-v8.fr-en.tok.fr
```

We run:
```
docker run -v $HOME/corpus:/corpus haukurp/moses-smt /bin/bash -c "/opt/moses/scripts/tokenizer/tokenizer.perl -l en \
    < /corpus/training/news-commentary-v8.fr-en.en  \
    > /corpus/news-commentary-v8.fr-en.tok.en" 

docker run -v $HOME/corpus:/corpus haukurp/moses-smt /bin/bash -c "/opt/moses/scripts/tokenizer/tokenizer.perl -l fr \
    < /corpus/training/news-commentary-v8.fr-en.fr    \
    > /corpus/news-commentary-v8.fr-en.tok.fr"
```
In short, we map the directory `$HOME/corpus` to the directory `/corpus` in the container 
and run `bash` (so that we can pipe, changing the original script as little as possible) 
the input and output to and from `tokenizer.perl`.
All the other commands can be executed in the same manner as described above.

When running scripts which require `-external-bin-dir`, for example `train-model.perl`,
 `-external-bin-dir` should take the argument `/opt/moses_tools`.
 To see the directories in `/opt` in the container, 
 run `docker run -v $HOME/corpus:/corpus haukurp/moses-smt ls /opt`
 
[GitHub repo of this project](https://github.com/cadia-lvl/SMT/tree/master/moses).

## Útgáfa
Keyra scriptu í þessari skrá með útgáfunúmeri. Sem dæmi: `docker-build.sh 1.1.1`.
Þetta mun þýða Moses og ýta myndinni á [DockerHub](https://hub.docker.com/r/haukurp/moses-smt) 
að því gefnu að notandinn hafi aðgang að DockerHub geymslunni.
Til að skrá sig inn í DockerHub þarf að gera `docker login` fyrst.
