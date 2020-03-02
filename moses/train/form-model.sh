#!/bin/bash
#SBATCH --job-name=moses-train
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=32GB
#SBATCH --time=8:01:00
#SBATCH --output=%j-%x.out
set -euxo

# check ENV vars
# echo $WORK_DIR
# echo $DATA_DIR

LOCAL=0
if [ "$LOCAL" = 1 ] ; then
  export THREADS=4
  export MEMORY=4096
  WORK_DIR="/home/haukur/work/"
else
  export THREADS="$SLURM_CPUS_PER_TASK"
  export MEMORY="$SLURM_MEM_PER_NODE"
  WORK_DIR="/work/haukurpj/"
  DATA_DIR="/work/haukurpj/data/mideind/"
fi

# Steps: 1=Prepare 2=LM 3=Train 4=Tune 5=Binarise 6=Translate 7=Evaluate
FIRST_STEP=1
LAST_STEP=4
# Constants
MOSES_TAG="1.1.0"
MOSESDECODER="/opt/moses"
MOSESDECODER_TOOLS="/opt/moses_tools"

# Model variables
LANG_FROM="en"
LANG_TO="is"
EXPERIMENT_NAME="form"

CLEAN_MIN_LENGTH=1
CLEAN_MAX_LENGTH=70
LM_SURFACE_ORDER=3
LM_POS_ORDER=3
ALIGNMENT="grow diag"
REORDERING="msd-bidirectional-fe"

TRAINING_DATA="$DATA_DIR"train/form-pos-lemma/data
DEV_DATA="$DATA_DIR"dev/form-pos-lemma/data
TEST_DIR_IN="$DATA_DIR"test/form-pos-lemma/
TEST_DIR_DETOK="$DATA_DIR"test/form-detok/

LM_SURFACE_TRAINING_DATA="$DATA_DIR"train/form/data
LM_SURFACE_TEST_DIR="$DATA_DIR"test/form/
LM_POS_TRAINING_DATA="$DATA_DIR"train/pos/data
LM_POS_TEST_DIR="$DATA_DIR"test/pos/

# Test if data is there
function check_data() {
  if [[ ! -f "$1" ]]; then
    echo "$1 does not exist. Exiting..."
    exit 1
  else
    wc -l "$1" 
    ls -hl "$1"
  fi
}

function check_dir_not_empty() {
  if [[ ! $(ls -A "$1") ]]; then
    echo "$1 is Empty"
    exit 1
  fi
}
check_data "$TRAINING_DATA".en
check_data "$TRAINING_DATA".is
check_data "$DEV_DATA".en
check_data "$DEV_DATA".is
check_dir_not_empty "$TEST_DIR_IN"
check_dir_not_empty "$TEST_DIR_DETOK"

check_data "$LM_SURFACE_TRAINING_DATA"."$LANG_TO"
check_dir_not_empty "$LM_SURFACE_TEST_DIR"
check_data "$LM_POS_TRAINING_DATA"."$LANG_TO"
check_dir_not_empty "$LM_POS_TEST_DIR"

# Variables for subsequent steps.
# 1. Prepare
  MODEL_NAME="$EXPERIMENT_NAME"-"$LANG_FROM"-"$LANG_TO"
  MODEL_DIR="$WORK_DIR""$MODEL_NAME"/
  MODEL_DATA_DIR="$MODEL_DIR"data/
  MODEL_RESULTS_DIR="$MODEL_DIR"results/
  CLEAN_DATA="$MODEL_DATA_DIR"train

# 2. Train LM
LM_SURFACE="$MODEL_DATA_DIR"form."$LANG_TO".blm
LM_POS="$MODEL_DATA_DIR"pos."$LANG_TO".blm

# 3. Train Moses
BASE_DIR="$MODEL_DIR"base
BASE_MOSES_INI="$BASE_DIR"model/moses.ini
BASE_PHRASE_TABLE="$BASE_DIR"model/phrase-table.gz
BASE_REORDERING_TABLE="$BASE_DIR"model/reordering-table.wbe-msd-bidirectional-fe.gz

# 4. Tune Moses
TUNE_DIR="$MODEL_DIR"tuned
TUNED_MOSES_INI="$TUNE_DIR"moses.ini

# 5. Binarise Moses
BINARISED_DIR="$MODEL_DIR"binarised/
BINARISED_MOSES_INI="$BINARISED_DIR"moses.ini
BINARISED_PHRASE_TABLE="$BINARISED_DIR"phrase-table
BINARISED_REORDERING_TABLE="$BINARISED_DIR"reordering-table
# TODO: Use many LMs
# BINARISED_LM="$BINARISED_DIR/lm.blm"

function run_in_singularity() {
  singularity exec \
  -B "$WORK_DIR":"$WORK_DIR" \
	docker://haukurp/moses-smt:"$MOSES_TAG" \
  "$@"
}

# Step=1. This script prepares all directories and cleans data
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
  rm -rf "$MODEL_DIR"
  mkdir -p "$MODEL_DIR"
  mkdir -p "$MODEL_DATA_DIR"
  mkdir -p "$MODEL_RESULTS_DIR"
  # Data prep
  run_in_singularity "$MOSESDECODER"/scripts/training/clean-corpus-n.perl "$TRAINING_DATA" "$LANG_FROM" "$LANG_TO" "$CLEAN_DATA" "$CLEAN_MIN_LENGTH" "$CLEAN_MAX_LENGTH"
fi

# LM creation
function train_lm() {
  LM_DATA="$1"
  LM="$2"
  LM_ORDER="$3"
  run_in_singularity "$MOSESDECODER"/bin/lmplz --order "$LM_ORDER" --temp_prefix "$WORK_DIR" -S 10G --discount_fallback <"$LM_DATA" >"$LM".arpa
  # we use the trie structure to save about 1/2 the space, but almost twice as slow
  # we use pointer compression to save more space, but slightly slower
  run_in_singularity "$MOSESDECODER"/bin/build_binary trie -a 64 -S 10G "$LM".arpa "$LM"
}

function eval_lm() {
  # LM evaluation, we evaluate on
  LM="$1"
  TEST_DIR="$2"
  for test_set in "$TEST_DIR"*."$LANG_TO"; do
    TEST_SET_NAME=$(basename "$test_set")
    run_in_singularity "$MOSESDECODER"/bin/query "$LM" <"$test_set" | tail -n 4 >"$MODEL_RESULTS_DIR""$TEST_SET_NAME".ppl
  done
}

# Step=2. Train LM
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
  train_lm "$LM_POS_TRAINING_DATA"."$LANG_TO" "$LM_POS" "$LM_POS_ORDER"
  eval_lm "$LM_POS" "$LM_POS_TEST_DIR"
  train_lm "$LM_SURFACE_TRAINING_DATA"."$LANG_TO" "$LM_SURFACE" "$LM_SURFACE_ORDER"
  eval_lm "$LM_SURFACE" "$LM_SURFACE_TEST_DIR"
fi

# Step=3. Train Moses factored model
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
  mkdir -p "$BASE_DIR"
  run_in_singularity "$MOSESDECODER"/scripts/training/train-model.perl \
    -root-dir "$BASE_DIR" \
    -corpus "$CLEAN_DATA" \
    -f "$LANG_FROM" \
    -e "$LANG_TO" \
    -alignment "$ALIGNMENT" \
    -reordering "$REORDERING" \
    -lm 0:"$LM_SURFACE_ORDER":"$LM_SURFACE":8 \
    -alignment-factors 0-0 \
    -reordering-factors 0-0 \
    -translation-factors 0-0 \
    -decoding-steps t0 \
    -mgiza \
    -mgiza-cpus "$THREADS" \
    -parallel \
    -sort-buffer-size "$MEMORY" \
    -sort-batch-size 1021 \
    -sort-compress gzip \
    -sort-parallel "$THREADS" \
    -cores "$THREADS" \
    -external-bin-dir "$MOSESDECODER_TOOLS"
fi

# Step=4 Tuning
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
  mkdir -p "$TUNE_DIR"
  run_in_singularity "$MOSESDECODER"/scripts/training/mert-moses.pl \
    "$DEV_DATA"."$LANG_FROM" \
    "$DEV_DATA"."$LANG_TO" \
    "$MOSESDECODER"/bin/moses "$BASE_MOSES_INI" \
    --mertdir "$MOSESDECODER"/bin \
    --working-dir "$TUNE_DIR" \
    --decoder-flags="-threads $THREADS"
fi

# Step=5. Binarise
if ((FIRST_STEP <= 5 && LAST_STEP >= 5)); then
  mkdir -p "$BINARISED_DIR"
  run_in_singularity "$MOSESDECODER"/bin/processPhraseTableMin \
    -in "$BASE_PHRASE_TABLE" \
    -nscores 4 \
    -out "$BINARISED_PHRASE_TABLE" \
    -threads "$THREADS"

  run_in_singularity "$MOSESDECODER"/bin/processLexicalTableMin \
    -in "$BASE_REORDERING_TABLE" \
    -out "$BINARISED_REORDERING_TABLE" \
    -threads "$THREADS"

  cp "$LM" "$BINARISED_LM"
  cp "$TUNED_MOSES_INI" "$BINARISED_MOSES_INI"
  # Adjust the path in the moses.ini file to point to the new files.
  sed -i "s|$LM|$BINARISED_LM|" $BINARISED_MOSES_INI
  sed -i "s|PhraseDictionaryMemory|PhraseDictionaryCompact|" $BINARISED_MOSES_INI
  sed -i "s|$BASE_PHRASE_TABLE|$BINARISED_PHRASE_TABLE|" $BINARISED_MOSES_INI
  sed -i "s|$BASE_REORDERING_TABLE|$BINARISED_REORDERING_TABLE|" $BINARISED_MOSES_INI
fi

# Step=6 Translate, post process and evaluate the test sets one by one.
# Be sure to activate the correct environment
if ((FIRST_STEP <= 6 && LAST_STEP >= 6)); then
  source /data/tools/anaconda/etc/profile.d/conda.sh
  conda activate notebook
  for test_set in "$TEST_DIR"*."$LANG_TO"; do
    TEST_SET_NAME=$(basename "$test_set")
    run_in_singularity /opt/moses/bin/moses -f "$BINARISED_DIR"moses.ini \
      -threads "$THREADS" \
      <"$test_set"."$LANG_FROM" \
      >"$MODEL_RESULTS_DIR""$TEST_SET_NAME"-translated."$LANG_FROM"-"$LANG_TO"

    frontend postprocess "$MODEL_RESULTS_DIR""$TEST_SET_NAME"-translated."$LANG_FROM"-"$LANG_TO" "$LANG_TO" v3 >"$MODEL_RESULTS_DIR""$TEST_SET_NAME"-translated-detok."$LANG_FROM"-"$LANG_TO"
    cat "$MODEL_RESULTS_DIR""$TEST_SET_NAME"-translated-detok."$LANG_FROM"-"$LANG_TO" >>"$MODEL_RESULTS_DIR"combined-translated-detok."$LANG_FROM"-"$LANG_TO"
    # TODO: Fix ground truth
    cat "$GROUND_TRUTH"-"$test_set"."$LANG_TO" >>"$MODEL_RESULTS_DIR"/test-combined."$LANG_TO"
  done
fi

# Step=7. Evaluate translations
if ((FIRST_STEP <= 7 && LAST_STEP >= 7)); then
  for test_set in "$TEST_DIR"*."$LANG_TO"; do
    TEST_SET_NAME=$(basename "$test_set")
    # TODO: Fix ground truth
    run_in_singularity /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
      "$GROUND_TRUTH"-"$test_set"."$LANG_TO" <"$MODEL_RESULTS_DIR""$TEST_SET_NAME"-translated-detok."$LANG_FROM"-"$LANG_TO" >"$MODEL_RESULTS_DIR""$TEST_SET_NAME"-"$LANG_FROM"-"$LANG_TO".bleu
  done
  # Score the combined translations
  run_in_singularity /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
    "$MODEL_RESULTS_DIR"test-combined."$LANG_TO" <"$MODEL_RESULTS_DIR"combined-translated-detok."$LANG_FROM"-"$LANG_TO" >"$MODEL_RESULTS_DIR"combined-"$LANG_FROM"-"$LANG_TO".bleu
fi
