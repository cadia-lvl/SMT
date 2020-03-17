#!/bin/bash
#SBATCH --job-name=moses-train
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=32G
#SBATCH --chdir=/home/staff/haukurpj/SMT
#SBATCH --time=8:01:00
#SBATCH --output=%j-%x.out
# e=fail on pipeline, u=fail on unset var, x=trace commands
set -ex

# check if script is started via SLURM or bash
# if with SLURM: there variable '$SLURM_JOB_ID' will exist
# `if [ -n $SLURM_JOB_ID ]` checks if $SLURM_JOB_ID is not an empty string
if [ -n "$SLURM_JOB_ID" ];  then
    THREADS="$SLURM_CPUS_PER_TASK"
    MEMORY="$SLURM_MEM_PER_NODE"
    WORK_DIR="/work/haukurpj/"
    DATA_DIR="/work/haukurpj/data/"
    #MOSESDECODER="/home/staff/haukurpj/moses"
    #MOSESDECODER_TOOLS="/home/staff/haukurpj/moses_tools"
    # check the original location through scontrol and $SLURM_JOB_ID
    # SCRIPT_PATH=$(scontrol show job "$SLURM_JOBID" | awk -F= '/Command=/{print $2}')
else
    # otherwise: started with bash. Get the real location.
    # SCRIPT_PATH=$(realpath "$0")
    THREADS=4
    MEMORY=4096
    WORK_DIR="/home/haukur/work/"
fi

# Steps: 1=Prepare 2=LM 3=Train 4=Tune 5=Binarise 6=Translate & Evaluate
FIRST_STEP=1
LAST_STEP=6

# Model variables
LANG_FROM="en"
LANG_TO="is"
EXPERIMENT_NAME="final"

CLEAN_MIN_LENGTH=1
CLEAN_MAX_LENGTH=70
LM_SURFACE_ORDER=5
ALIGNMENT="grow-diag"
REORDERING="msd-bidirectional-fe"

TRAINING_DATA="$DATA_DIR"train/form/data
DEV_DATA_IN="$DATA_DIR"dev/form/data
DEV_DATA_OUT="$DATA_DIR"dev/form/data
TEST_DIR_IN="$DATA_DIR"test/form/
TEST_DIR_DETOK="$DATA_DIR"test/form-detok/

LM_SURFACE_TRAINING_DATA="$DATA_DIR"train/form/data-lm.is
LM_SURFACE_TEST_DIR="$DATA_DIR"test/form/

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
check_data "$DEV_DATA_IN"."$LANG_FROM"
check_data "$DEV_DATA_OUT"."$LANG_TO"
check_dir_not_empty "$TEST_DIR_IN"
check_dir_not_empty "$TEST_DIR_DETOK"

check_data "$LM_SURFACE_TRAINING_DATA"
check_dir_not_empty "$LM_SURFACE_TEST_DIR"

# Variables for subsequent steps.
# 1. Prepare
MODEL_NAME="$EXPERIMENT_NAME"-"$LANG_FROM"-"$LANG_TO"
MODEL_DIR="$WORK_DIR""$MODEL_NAME"/
MODEL_DATA_DIR="$MODEL_DIR"data/
MODEL_RESULTS_DIR="$MODEL_DIR"results/
CLEAN_DATA="$MODEL_DATA_DIR"train

# 2. Train LM
LM_SURFACE="$MODEL_DATA_DIR"form."$LANG_TO".blm

# 3. Train Moses
BASE_DIR="$MODEL_DIR"base/
BASE_MOSES_INI="$BASE_DIR"model/moses.ini
BASE_PHRASE_TABLE="$BASE_DIR"model/phrase-table.gz
BASE_REORDERING_TABLE="$BASE_DIR"model/reordering-table.wbe-msd-bidirectional-fe.gz

# 4. Tune Moses
TUNE_DIR="$MODEL_DIR"tuned/
TUNED_MOSES_INI="$TUNE_DIR"moses.ini

# 5. Binarise Moses
BINARISED_DIR="$MODEL_DIR"binarised/

# Step=1. This script prepares all directories and cleans data
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
  rm -rf "$MODEL_DIR"
  mkdir -p "$MODEL_DIR"
  mkdir -p "$MODEL_DATA_DIR"
  mkdir -p "$MODEL_RESULTS_DIR"
  # Data prep
  "$MOSESDECODER"/scripts/training/clean-corpus-n.perl "$TRAINING_DATA" "$LANG_FROM" "$LANG_TO" "$CLEAN_DATA" "$CLEAN_MIN_LENGTH" "$CLEAN_MAX_LENGTH"
fi

# Step=2. Train LM
function train_lm() {
  LM_DATA="$1"
  LM="$2"
  LM_ORDER="$3"
  "$MOSESDECODER"/bin/lmplz --order "$LM_ORDER" --temp_prefix "$WORK_DIR" -S 30G --discount_fallback <"$LM_DATA" >"$LM".arpa
  # we use the trie structure to save about 1/2 the space, but almost twice as slow `trie`
  # we use pointer compression to save more space, but slightly slower `-a 64`
  "$MOSESDECODER"/bin/build_binary trie -a 64 -S 30G "$LM".arpa "$LM"
}

function eval_lm() {
  # LM evaluation, we evaluate on
  LM="$1"
  TEST_DIR="$2"
  for test_set in "$TEST_DIR"*."$LANG_TO"; do
    TEST_SET_NAME=$(basename "$test_set")
    "$MOSESDECODER"/bin/query "$LM" <"$test_set" | tail -n 4 >"$MODEL_RESULTS_DIR""$TEST_SET_NAME".ppl
  done
}

if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
  train_lm "$LM_SURFACE_TRAINING_DATA" "$LM_SURFACE" "$LM_SURFACE_ORDER"
  eval_lm "$LM_SURFACE" "$LM_SURFACE_TEST_DIR"
fi

# Step=3. Train Moses model
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
  mkdir -p "$BASE_DIR"
  "$MOSESDECODER"/scripts/training/train-model.perl \
    -root-dir "$BASE_DIR" \
    -corpus "$CLEAN_DATA" \
    -f "$LANG_FROM" \
    -e "$LANG_TO" \
    -alignment "$ALIGNMENT" \
    -reordering "$REORDERING" \
    -lm 0:"$LM_SURFACE_ORDER":"$LM_SURFACE":8 \
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
  # When tuning over factors, it is best to skip the filtering.
  "$MOSESDECODER"/scripts/training/mert-moses.pl \
    "$DEV_DATA_IN"."$LANG_FROM" \
    "$DEV_DATA_OUT"."$LANG_TO" \
    "$MOSESDECODER"/bin/moses "$BASE_MOSES_INI" \
    --mertdir "$MOSESDECODER"/bin \
    --working-dir "$TUNE_DIR" \
    --decoder-flags="-threads $THREADS"
fi

# Step=5. Binarise
function binarise_table() {
  PHRASE_TABLE_IN=$1
  BINARISED_PHRASE_TABLE_OUT=$2
  REORDERING_TABLE_IN=$3
  BINARISED_REORDERING_TABLE_OUT=$4

  "$MOSESDECODER"/bin/processPhraseTableMin \
    -in "$PHRASE_TABLE_IN" \
    -nscores 4 \
    -out "$BINARISED_PHRASE_TABLE_OUT" \
    -threads "$THREADS"

  "$MOSESDECODER"/bin/processLexicalTableMin \
    -in "$REORDERING_TABLE_IN" \
    -out "$BINARISED_REORDERING_TABLE_OUT" \
    -threads "$THREADS"
}

function fix_paths() {
  PATH_IN=$1
  PATH_OUT=$2
  FILE=$3
  sed -i "s|$PATH_IN|$PATH_OUT|" "$FILE"
  # Adjust the path in the moses.ini file to point to the new files.
}

if ((FIRST_STEP <= 5 && LAST_STEP >= 5)); then
  mkdir -p "$BINARISED_DIR"
  # TODO: Use many LMs
  BINARISED_LM="$BINARISED_DIR"lm.blm
  BINARISED_MOSES_INI="$BINARISED_DIR"moses.ini
  BINARISED_PHRASE_TABLE="$BINARISED_DIR"phrase-table
  BINARISED_REORDERING_TABLE="$BINARISED_DIR"reordering-table
  binarise_table "$BASE_PHRASE_TABLE" "$BINARISED_PHRASE_TABLE" "$BASE_REORDERING_TABLE" "$BINARISED_REORDERING_TABLE"
  cp "$LM_SURFACE" "$BINARISED_LM"
  cp "$TUNED_MOSES_INI" "$BINARISED_MOSES_INI"
  fix_paths $LM_SURFACE $BINARISED_LM $BINARISED_MOSES_INI
  fix_paths $BASE_PHRASE_TABLE $BINARISED_PHRASE_TABLE $BINARISED_MOSES_INI
  fix_paths $BASE_REORDERING_TABLE $BINARISED_REORDERING_TABLE $BINARISED_MOSES_INI
  sed -i "s|PhraseDictionaryMemory|PhraseDictionaryCompact|" $BINARISED_MOSES_INI
fi

# Step=6 Translate and post-process.
# Be sure to activate the correct environment
if ((FIRST_STEP <= 6 && LAST_STEP >= 6)); then
  source /data/tools/anaconda/etc/profile.d/conda.sh
  # TODO: Somehow check the environment to begin with
  conda activate notebook
  TEST_SET_TRANSLATED_COMBINED="$MODEL_RESULTS_DIR"combined-translated-detok."$LANG_TO"
  TEST_SET_CORRECT_COMBINED="$MODEL_RESULTS_DIR"combined-detok."$LANG_TO"
  TEST_SET_COMBINED_BLUE_SCORE="$MODEL_RESULTS_DIR"combined."$LANG_FROM"-"$LANG_TO".bleu
  rm "$TEST_SET_CORRECT_COMBINED" || true
  rm "$TEST_SET_TRANSLATED_COMBINED" || true
  declare -a test_sets=(
        "test-ees"
        "test-ema"
        "test-opensubtitles"
  )
  for test_set in "${test_sets[@]}"; do
    TEST_SET_CORRECT="$TEST_DIR_IN""$test_set"."$LANG_TO"
    TEST_SET_CORRECT_POSTPROCESSED="$MODEL_RESULTS_DIR""$test_set"-detok."$LANG_TO"
    TEST_SET_IN="$TEST_DIR_IN""$test_set"."$LANG_FROM"
    TEST_SET_TRANSLATED="$MODEL_RESULTS_DIR""$test_set"-translated."$LANG_FROM"-"$LANG_TO"
    TEST_SET_TRANSLATED_POSTPROCESSED="$MODEL_RESULTS_DIR""$test_set"-translated-detok."$LANG_FROM"-"$LANG_TO"
    TEST_SET_BLUE_SCORE="$MODEL_RESULTS_DIR""$test_set"."$LANG_FROM"-"$LANG_TO".bleu
    # Translate
    /opt/moses/bin/moses -f "$BINARISED_DIR"moses.ini \
      -threads "$THREADS" \
      < "$TEST_SET_IN" \
      >"$TEST_SET_TRANSLATED"
    # Postprocess
    preprocessing/main.py postprocess "$TEST_SET_TRANSLATED" "$TEST_SET_TRANSLATED_POSTPROCESSED" $LANG_TO
    preprocessing/main.py postprocess "$TEST_SET_CORRECT" "$TEST_SET_CORRECT_POSTPROCESSED" $LANG_TO

    # Combine
    cat "$TEST_SET_TRANSLATED_POSTPROCESSED" >> "$TEST_SET_TRANSLATED_COMBINED"
    cat "$TEST_SET_CORRECT_POSTPROCESSED" >> "$TEST_SET_CORRECT_COMBINED"
    # Evaluate
    /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
      "$TEST_SET_TRANSLATED_POSTPROCESSED" \
       < "$TEST_SET_CORRECT_POSTPROCESSED" \
       > "$TEST_SET_BLUE_SCORE"
  done
  # The combined
  /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
    "$TEST_SET_TRANSLATED_COMBINED" \
     < "$TEST_SET_CORRECT_COMBINED" \
     > "$TEST_SET_COMBINED_BLUE_SCORE"
fi
