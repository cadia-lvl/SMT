#!/bin/bash
#SBATCH --job-name=moses-binarise
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=16GB
#SBATCH --time=1:00:00
set -euxo

dir_name=~/SMT/moses_model
source "$dir_name"/moses-definitions.sh

# Binarise
mkdir -p ${BINARISED_DIR}
run_in_singularity ${MOSESDECODER}/bin/processPhraseTableMin \
        -in $BASE_PHRASE_TABLE \
        -nscores 4 \
        -out $BINARISED_PHRASE_TABLE \
        -threads $THREADS

run_in_singularity ${MOSESDECODER}/bin/processLexicalTableMin \
        -in $BASE_REORDERING_TABLE \
        -out $BINARISED_REORDERING_TABLE \
        -threads $THREADS

cp $LM $BINARISED_LM
cp $TUNED_MOSES_INI $BINARISED_MOSES_INI
# Adjust the path in the moses.ini file to point to the new files.
sed -i "s|$LM|$BINARISED_LM|" $BINARISED_MOSES_INI
sed -i "s|PhraseDictionaryMemory|PhraseDictionaryCompact|" $BINARISED_MOSES_INI
sed -i "s|$BASE_PHRASE_TABLE|$BINARISED_PHRASE_TABLE|" $BINARISED_MOSES_INI
sed -i "s|$BASE_REORDERING_TABLE|$BINARISED_REORDERING_TABLE|" $BINARISED_MOSES_INI


