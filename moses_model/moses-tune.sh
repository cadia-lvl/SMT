#!/bin/bash
#SBATCH --job-name=moses-tune
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=10GB
#SBATCH --time=3:00:00
set -euxo

dir_name=$(dirname "$0")
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


