#!/bin/bash
#SBATCH --job-name=moses-evaluate
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=10GB
#SBATCH --time=2:00:00
#SBATCH --output=/home/staff/haukurpj/%j-%x.out
set -exo

source $1
# Translate, post process and evaluate the test sets one by one.
# Be sure to activate the correct environment
source /data/tools/anaconda/etc/profile.d/conda.sh
conda activate notebook
for test_set in $TEST_SETS; do
  run_in_singularity /opt/moses/bin/moses -f $BINARISED_DIR/moses.ini \
    -threads $THREADS \
    <$TEST_INPUT-$test_set.$LANG_FROM \
    >$MODEL_RESULTS/$test_set-translated.$LANG_FROM-$LANG_TO

  frontend postprocess $MODEL_RESULTS/$test_set-translated.$LANG_FROM-$LANG_TO $LANG_TO v3 >$MODEL_RESULTS/$test_set-translated-detok.$LANG_FROM-$LANG_TO
  cat $MODEL_RESULTS/$test_set-translated-detok.$LANG_FROM-$LANG_TO >>$MODEL_RESULTS/combined-translated-detok.$LANG_FROM-$LANG_TO
  cat $GROUND_TRUTH-$test_set.$LANG_TO >>$MODEL_RESULTS/test-combined.$LANG_TO
  run_in_singularity /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
    $GROUND_TRUTH-$test_set.$LANG_TO <$MODEL_RESULTS/$test_set-translated-detok.$LANG_FROM-$LANG_TO >$MODEL_RESULTS/$test_set-$LANG_FROM-$LANG_TO.bleu
done

# Score the combined translations
run_in_singularity /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
  $MODEL_RESULTS/test-combined.$LANG_TO <$MODEL_RESULTS/combined-translated-detok.$LANG_FROM-$LANG_TO >$MODEL_RESULTS/combined-$LANG_FROM-$LANG_TO.bleu
