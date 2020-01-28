#!/bin/bash

# Define Moses parameters and variables
set -exo
LOCAL=0
if [ $LOCAL = 1 ] ; then
  export THREADS=4
  export MEMORY=4096
  WORK_DIR="/home/haukur/work"
else
  export THREADS=$SLURM_CPUS_PER_TASK
  export MEMORY=$SLURM_MEM_PER_NODE
  WORK_DIR="/work/haukurpj"
fi

# Constants
MOSES_TAG="1.1.0"
MOSESDECODER="/opt/moses"
MOSESDECODER_TOOLS="/opt/moses_tools"

# Define variables
LANG_FROM="en"
LANG_TO="is"
EXPERIMENT_NAME="new-test"

CLEAN_MIN_LENGTH=1
CLEAN_MAX_LENGTH=70
LM_ORDER=3
ALIGNMENT="grow diag"
REORDERING="msd-bidirectional-fe"

TRAINING_DATA="${WORK_DIR}/data/mapped/Parice1.0/train"
DEV_DATA="${WORK_DIR}/data/mapped/Parice1.0/dev"
TEST_SETS="ees ema opensubtitles"
TEST_INPUT="${WORK_DIR}/data/mapped/Parice1.0/test"
GROUND_TRUTH="${WORK_DIR}/data/filtered/Parice1.0/test"
# Set LM_EXTRA_DATA to "" if no extra lm data.
# LM_EXTRA_DATA="${DATA_DIR}/rmh-final.is"
# LM_EXTRA_DATA="${DATA_DIR}/mono-final.en"
LM_EXTRA_DATA=""

# Test if data is there
function check_data() {
  if [ ! -f $1 ]; then
    echo "$1 does not exist. Exiting..."
    exit 1
  else
    wc -l $1 
    ls -hl $1
  fi
}
check_data $TRAINING_DATA.en
check_data $TRAINING_DATA.is
check_data $DEV_DATA.en
check_data $DEV_DATA.is
for test_set in $TEST_SETS; do
  check_data $TEST_INPUT-$test_set.$LANG_FROM
  check_data $GROUND_TRUTH-$test_set.$LANG_TO
done

# Variables for subsequent steps.
MODEL_NAME="${EXPERIMENT_NAME}-${LANG_FROM}-${LANG_TO}"
MODEL_DIR=$WORK_DIR/$MODEL_NAME
MODEL_DATA="${MODEL_DIR}/data"
MODEL_RESULTS="$MODEL_DIR/results"
CLEAN_DATA="$MODEL_DATA/train"
LM="$MODEL_DATA/$LANG_TO.blm"

BASE_DIR="${MODEL_DIR}/base"
BASE_MOSES_INI="${BASE_DIR}/model/moses.ini"
BASE_PHRASE_TABLE="${BASE_DIR}/model/phrase-table.gz"
BASE_REORDERING_TABLE="${BASE_DIR}/model/reordering-table.wbe-msd-bidirectional-fe.gz"

TUNE_DIR="${MODEL_DIR}/tuned"
TUNED_MOSES_INI="${TUNE_DIR}/moses.ini"

BINARISED_DIR="${MODEL_DIR}/binarised"
BINARISED_MOSES_INI="${BINARISED_DIR}/moses.ini"
BINARISED_PHRASE_TABLE="${BINARISED_DIR}/phrase-table"
BINARISED_REORDERING_TABLE="${BINARISED_DIR}/reordering-table"
BINARISED_LM="$BINARISED_DIR/lm.blm"


function run_in_singularity() {
  singularity exec \
  -B $WORK_DIR:$WORK_DIR \
	docker://haukurp/moses-smt:$MOSES_TAG \
  "$@"
}

