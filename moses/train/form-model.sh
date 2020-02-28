#!/bin/bash
#SBATCH --job-name=moses-train
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=32GB
#SBATCH --time=8:01:00
#SBATCH --output=%j-%x.out
set -euxo

# check ENV vars
echo $WORK_DIR
echo $DATA_DIR

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

jid_prep=$(sbatch --partition=longrunning $dir_name/moses-prep.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
jid_lm=$(sbatch --partition=longrunning --dependency=afterok:$jid_prep $dir_name/moses-lm.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
jid_train=$(sbatch --partition=longrunning --dependency=afterok:$jid_lm $dir_name/moses-train-factored.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
jid_tune=$(sbatch --partition=longrunning --dependency=afterok:$jid_train $dir_name/moses-tune.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
#jid_binarise=$(sbatch --partition=longrunning --dependency=afterok:$jid_tune $dir_name/moses-binarise.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
#jid_translate=$(sbatch --partition=longrunning --dependency=afterok:$jid_binarise $dir_name/moses-translate.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
#jid_evaluate=$(sbatch --partition=longrunning --dependency=afterok:$jid_translate $dir_name/moses-evaluate.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
echo "$jid_evaluate"#!/bin/bash

# Constants
MOSES_TAG="1.1.0"
MOSESDECODER="/opt/moses"
MOSESDECODER_TOOLS="/opt/moses_tools"

# Model variables
LANG_FROM="en"
LANG_TO="is"
EXPERIMENT_NAME="morph"

CLEAN_MIN_LENGTH=1
CLEAN_MAX_LENGTH=70
LM_ORDER_SURFACE=3
LM_ORDER_POS=3
ALIGNMENT="grow diag"
REORDERING="msd-bidirectional-fe"

TRAINING_DATA="${WORK_DIR}/data/mideind/train.form.pos.lemma"
TRAINING_DATA_LM_SURFACE="${WORK_DIR}/data/mideind/train.form"
TRAINING_DATA_LM_POS="${WORK_DIR}/data/mideind/train.pos"
DEV_DATA="${WORK_DIR}/data/mideind/dev.form.pos.lemma"
TEST_INPUTS="${WORK_DIR}/data/mideind/test-ees.form.pos.lemma.$LANG_FROM ${WORK_DIR}/data/mideind/test-ema.form.pos.lemma.$LANG_FROM ${WORK_DIR}/data/mideind/test-opensubtitles.form.pos.lemma.$LANG_FROM"
TEST_OUTPUTS="${WORK_DIR}/data/mideind/test-ees.form.detok.$LANG_TO ${WORK_DIR}/data/mideind/test-ema.form.detok.$LANG_TO ${WORK_DIR}/data/mideind/test-opensubtitles.form.detok.$LANG_TO"
TEST_LM_SURFACE="${WORK_DIR}/data/mideind/test-ees.form ${WORK_DIR}/data/mideind/test-ema.form ${WORK_DIR}/data/mideind/test-opensubtitles.form"
TEST_LM_POS="${WORK_DIR}/data/mideind/test-ees.pos ${WORK_DIR}/data/mideind/test-ema.pos ${WORK_DIR}/data/mideind/test-opensubtitles.pos"

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
check_data $TRAINING_DATA_LM_POS.$LANG_TO
check_data $TRAINING_DATA_LM_SURFACE.$LANG_TO
check_data $DEV_DATA.en
check_data $DEV_DATA.is
for test_set in $TEST_INPUTS; do
  check_data $test_set
done
for test_set in $TEST_OUTPUTS; do
  check_data $test_set
done
for test_set in $TEST_LM_POS; do
  check_data $test_set.$LANG_TO
done
for test_set in $TEST_LM_SURFACE; do
  check_data $test_set.$LANG_TO
done

# Variables for subsequent steps.
MODEL_NAME="${EXPERIMENT_NAME}-${LANG_FROM}-${LANG_TO}"
MODEL_DIR=$WORK_DIR/$MODEL_NAME
MODEL_DATA="${MODEL_DIR}/data"
MODEL_RESULTS="$MODEL_DIR/results"
CLEAN_DATA="$MODEL_DATA/train"
LM_SURFACE="$MODEL_DATA/form.$LANG_TO.blm"
LM_POS="$MODEL_DATA/pos.$LANG_TO.blm"

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

# This script prepares all directories and writes the description of the model hyperparameters to a file.
mkdir -p $MODEL_DIR
mkdir -p $MODEL_DATA
mkdir -p $MODEL_RESULTS

# Data prep
run_in_singularity ${MOSESDECODER}/scripts/training/clean-corpus-n.perl $TRAINING_DATA $LANG_FROM $LANG_TO $CLEAN_DATA $CLEAN_MIN_LENGTH $CLEAN_MAX_LENGTH

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

# Train Moses factored model
mkdir -p ${BASE_DIR}
run_in_singularity ${MOSESDECODER}/scripts/training/train-model.perl \
  -root-dir $BASE_DIR \
  -corpus $CLEAN_DATA \
  -f $LANG_FROM \
  -e $LANG_TO \
  -alignment $ALIGNMENT \
  -reordering $REORDERING \
  -lm 0:${LM_ORDER_SURFACE}:${LM_SURFACE}:8 \
  -lm 1:${LM_ORDER_POS}:${LM_POS}:8 \
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
  -external-bin-dir $MOSESDECODER_TOOLS#!/bin/bash

# Tuning
mkdir -p ${TUNE_DIR}
run_in_singularity ${MOSESDECODER}/scripts/training/mert-moses.pl \
  "$DEV_DATA.$LANG_FROM" \
  "$DEV_DATA.$LANG_TO" \
  ${MOSESDECODER}/bin/moses $BASE_MOSES_INI \
  --mertdir ${MOSESDECODER}/bin \
  --working-dir $TUNE_DIR \
  --decoder-flags="-threads $THREADS"

# Binarise
mkdir -p ${BINARISED_DIR}
run_in_singularity ${MOSESDECODER}/bin/processPhraseTableMin \
  -in $BASE_PHRASE_TABLE \
  -nscores 4 \
  -out $BINARISED_PHRASE_TABLE \
  -threads $THREADS

run_in_singularity ${MOSESDECODER}/bin/processLexicalTableMin \
  -in $BASE_REORDERING_TABLE \
  -out $BINARISED_REORDERING_TABLE \
  -threads $THREADS

cp $LM $BINARISED_LM
cp $TUNED_MOSES_INI $BINARISED_MOSES_INI
# Adjust the path in the moses.ini file to point to the new files.
sed -i "s|$LM|$BINARISED_LM|" $BINARISED_MOSES_INI
sed -i "s|PhraseDictionaryMemory|PhraseDictionaryCompact|" $BINARISED_MOSES_INI
sed -i "s|$BASE_PHRASE_TABLE|$BINARISED_PHRASE_TABLE|" $BINARISED_MOSES_INI
sed -i "s|$BASE_REORDERING_TABLE|$BINARISED_REORDERING_TABLE|" $BINARISED_MOSES_INI

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
done

# Evaluate translations
for test_set in $TEST_SETS; do
  run_in_singularity /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
    $GROUND_TRUTH-$test_set.$LANG_TO <$MODEL_RESULTS/$test_set-translated-detok.$LANG_FROM-$LANG_TO >$MODEL_RESULTS/$test_set-$LANG_FROM-$LANG_TO.bleu
done

# Score the combined translations
run_in_singularity /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
  $MODEL_RESULTS/test-combined.$LANG_TO <$MODEL_RESULTS/combined-translated-detok.$LANG_FROM-$LANG_TO >$MODEL_RESULTS/combined-$LANG_FROM-$LANG_TO.bleu
