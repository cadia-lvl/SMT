#!/bin/bash
#SBATCH --job-name=moses-train
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=10GB
#SBATCH --time=6:00:00

set -euxo

source $1
# Train Moses factored model
mkdir -p ${BASE_DIR}
run_in_singularity ${MOSESDECODER}/scripts/training/train-model.perl \
  -root-dir $BASE_DIR \
  -corpus $CLEAN_DATA \
  -f $LANG_FROM \
  -e $LANG_TO \
  -input-factor-max 2 \
  -alignment $ALIGNMENT \
  -reordering $REORDERING \
  -lm 0:${LM_ORDER_SURFACE}:${LM_SURFACE}:8 \
  -lm 2:${LM_ORDER_POS}:${LM_POS}:8 \
  -reordering-factors 0-0+2-2 \
  -translation-factors 1-1+2-2+0-0,2 \
  -generation-factors 1-2+1,2-0 \
  -decoding-steps t0,g0,t1,g1:t2 \
  -mgiza \
  -mgiza-cpus "$THREADS" \
  -parallel \
  -sort-buffer-size "$MEMORY" \
  -sort-batch-size 1021 \
  -sort-compress gzip \
  -sort-parallel "$THREADS" \
  -cores "$THREADS" \
  -external-bin-dir $MOSESDECODER_TOOLS
