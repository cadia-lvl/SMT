#!/bin/bash
#SBATCH --job-name=moses-lm
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=10GB
#SBATCH --time=2:00:00

set -euxo

source $1
# LM creation
function train_lm() {
  LM_DATA=$1
  LM=$2
  LM_ORDER=$3
  run_in_singularity ${MOSESDECODER}/bin/lmplz --order $LM_ORDER --temp_prefix $WORK_DIR/ -S 10G --discount_fallback <${LM_DATA} >${LM}.arpa
  run_in_singularity ${MOSESDECODER}/bin/build_binary -S 10G ${LM}.arpa ${LM}
}

function eval_lm() {
  # LM evaluation, we evaluate on
  LM=$1
  TEST_LM=$2
  for test_set in $TEST_LM; do
    TEST_SET_NAME=$(basename $test_set)
    run_in_singularity ${MOSESDECODER}/bin/query ${LM} <$test_set.$LANG_TO | tail -n 4 >$MODEL_RESULTS/$TEST_SET_NAME.ppl
  done
}
train_lm $TRAINING_DATA_LM_POS.$LANG_TO $LM_POS $LM_ORDER_POS
eval_lm $LM_POS $TEST_LM_POS
train_lm $TRAINING_DATA_LM_SURFACE.$LANG_TO $LM_SURFACE $LM_ORDER_SURFACE
eval_lm $LM_SURFACE $TEST_LM_SURFACE
