#!/bin/bash
#SBATCH --job-name=moses-evaluate
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=10GB
#SBATCH --time=2:00:00

set -exo

source $1
for test_set in $TEST_SETS; do
  run_in_singularity /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
    $GROUND_TRUTH-$test_set.$LANG_TO <$MODEL_RESULTS/$test_set-translated-detok.$LANG_FROM-$LANG_TO >$MODEL_RESULTS/$test_set-$LANG_FROM-$LANG_TO.bleu
done

# Score the combined translations
run_in_singularity /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
  $MODEL_RESULTS/test-combined.$LANG_TO <$MODEL_RESULTS/combined-translated-detok.$LANG_FROM-$LANG_TO >$MODEL_RESULTS/combined-$LANG_FROM-$LANG_TO.bleu
