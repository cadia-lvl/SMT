#!/bin/bash
#SBATCH --job-name=moses-tune
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=16GB
#SBATCH --time=2:00:00
#SBATCH --output=/home/staff/haukurpj/%j-%x.out
set -euxo

dir_name=~/SMT/moses_model
source "$dir_name"/moses-definitions.sh

# Tuning
mkdir -p ${TUNE_DIR}
run_in_singularity ${MOSESDECODER}/scripts/training/mert-moses.pl \
        "$DEV_DATA.$LANG_FROM" \
        "$DEV_DATA.$LANG_TO" \
        ${MOSESDECODER}/bin/moses $BASE_MOSES_INI \
        --mertdir ${MOSESDECODER}/bin \
        --working-dir $TUNE_DIR \
        --decoder-flags="-threads $THREADS"


