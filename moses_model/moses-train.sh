#!/bin/bash
#SBATCH --job-name=moses-train
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=10GB
#SBATCH --time=5:00:00
#SBATCH --output=/home/staff/haukurpj/%j-%x.out
set -euxo

dir_name=~/SMT/moses_model
source "$dir_name"/moses-definitions.sh

# Train Moses
mkdir -p ${BASE_DIR}
run_in_singularity ${MOSESDECODER}/scripts/training/train-model.perl -root-dir $BASE_DIR \
        -corpus $CLEAN_DATA \
        -f $LANG_FROM \
        -e $LANG_TO \
        -alignment $ALIGNMENT -reordering $REORDERING \
        -lm 0:${LM_ORDER}:${LM}:8 \
        -mgiza -mgiza-cpus "$THREADS" \
        -parallel -sort-buffer-size "$MEMORY" -sort-batch-size 1021 \
        -sort-compress gzip -sort-parallel "$THREADS" \
        -cores "$THREADS" \
        -external-bin-dir $MOSESDECODER_TOOLS

