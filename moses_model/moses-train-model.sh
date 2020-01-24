#!/bin/bash
#SBATCH --job-name=train-moses
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=16GB
#SBATCH --time=7:00:00
set -euxo
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

LANG_FROM="en"
LANG_TO="is"
EXPERIMENT_NAME="new-test"

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
    echo "File does not exist. Exiting..."
    exit 1
  fi
}
check_data $TRAINING_DATA.en
check_data $TRAINING_DATA.is
check_data $DEV_DATA.en
check_data $DEV_DATA.is
for test_set in $TEST_SETS; do
  check_data $TEST_INPUT-$test_set.$FROM
  check_data $GROUND_TRUTH-$test_set.$TO
done

# Setup everything
MODEL_NAME="${EXPERIMENT_NAME}-${LANG_FROM}-${LANG_TO}"
MODEL_DIR=$WORKING_DIR/$MODEL_NAME
mkdir $MODEL_DIR
MODEL_DATA="${MODEL_DIR}/data"
mkdir $MODEL_DATA
MODEL_RESULTS="$MODEL_DIR/results"
mkdir $MODEL_RESULTS
CLEAN_DATA="$MODEL_DATA/train"
LM="$MODEL_DATA/$TO.blm"

CLEAN_MIN_LENGTH=1
CLEAN_MAX_LENGTH=70
LM_ORDER=3
ALIGNMENT="grow diag"
REORDERING="msd-bidirectional-fe"

echo "name=$EXPERIMENT_NAME
from=$FROM
to=$TO
lm_extra=$LM_EXTRA_DATA
train=$TRAINING_DATA
dev=$DEV_DATA
test=$TEST_INPUT
ground-truth=$GROUND_TRUTH
clean_min=$CLEAN_MIN_LENGTH
clean_max=$CLEAN_MAX_LENGTH
lm_order=$LM_ORDER
alignment=$ALIGNMENT" > $MODEL_DIR/description.txt

MOSES_TAG="1.1.0"
MOSESDECODER="/opt/moses"
MOSESDECODER_TOOLS="/opt/moses_tools"

function run_in_singularity() {
  singularity exec \
  -B $WORK_DIR:$WORK_DIR \
	docker://haukurp/moses-smt:$MOSES_TAG \
  "$@"
}

# Data prep
run_in_singularity ${MOSESDECODER}/scripts/training/clean-corpus-n.perl $TRAINING_DATA $LANG_FROM $LANG_TO $CLEAN_DATA $CLEAN_MIN_LENGTH $CLEAN_MAX_LENGTH

# LM creation
LM_DATA=${DATA_DIR}/${MODEL_NAME}-lm.${LANG_TO}
cat ${CLEAN_DATA}.${LANG_TO} $LM_EXTRA_DATA > $LM_DATA
run_in_singularity ${MOSESDECODER}/bin/lmplz --order $LM_ORDER --temp_prefix $WORKING_DIR/ --memory 50% --discount_fallback < ${LM_DATA} > ${LM}.arpa
run_in_singularity ${MOSESDECODER}/bin/build_binary -S 50% ${LM}.arpa ${LM}

# Training
BASE_DIR="${MODEL_DIR}/base"
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


BASE_MOSES_INI="${BASE_DIR}/model/moses.ini"
BASE_PHRASE_TABLE="${BASE_DIR}/model/phrase-table.gz"
BASE_REORDERING_TABLE="${BASE_DIR}/model/reordering-table.wbe-msd-bidirectional-fe.gz"

# Tuning
TUNE_DIR="${MODEL_DIR}/tuned"
mkdir -p ${TUNE_DIR}
run_in_singularity ${MOSESDECODER}/scripts/training/mert-moses.pl \
        "$VALIDATION_DATA.$LANG_FROM" \
        "$VALIDATION_DATA.$LANG_TO" \
        ${MOSESDECODER}/bin/moses $BASE_MOSES_INI \
        --mertdir ${MOSESDECODER}/bin \
        --working-dir $TUNE_DIR \
        --decoder-flags="-threads $THREADS"

TUNED_MOSES_INI="${TUNE_DIR}/moses.ini"

# Binarise
BINARISED_DIR="${MODEL_DIR}/binarised"
mkdir -p ${BINARISED_DIR}
BINARISED_MOSES_INI="${BINARISED_DIR}/moses.ini"
BINARISED_PHRASE_TABLE="${BINARISED_DIR}/phrase-table"
BINARISED_REORDERING_TABLE="${BINARISED_DIR}/reordering-table"
BINARISED_LM="$BINARISED_DIR/lm.blm"

run_in_singularity ${MOSESDECODER}/bin/processPhraseTableMin \
        -in $BASE_PHRASE_TABLE \
        -nscores 4 \
        -out $BINARISED_PHRASE_TABLE

run_in_singularity ${MOSESDECODER}/bin/processLexicalTableMin \
        -in $BASE_REORDERING_TABLE \
        -out $BINARISED_REORDERING_TABLE

cp $LM $BINARISED_LM
cp $TUNED_MOSES_INI $BINARISED_MOSES_INI
# Adjust the path in the moses.ini file to point to the new files.
sed -i "s|$LM|$BINARISED_LM|" $BINARISED_MOSES_INI
sed -i "s|PhraseDictionaryMemory|PhraseDictionaryCompact|" $BINARISED_MOSES_INI
sed -i "s|$BASE_PHRASE_TABLE|$BINARISED_PHRASE_TABLE|" $BINARISED_MOSES_INI
sed -i "s|$BASE_REORDERING_TABLE|$BINARISED_REORDERING_TABLE|" $BINARISED_MOSES_INI

# Translate, post process and evaluate the test sets one by one.
for test_set in $TEST_SETS; do
  singularity run \
    -B $WORKING_DIR:$WORKING_DIR \
     docker://haukurp/moses-smt:1.1.0 \
     /opt/moses/bin/moses -f $BINARISED_DIR/moses.ini \
     -threads $THREADS \
      < $TEST_INPUT-$test_set.$FROM \
      > $MODEL_RESULTS/$test_set-translated.$FROM-$TO

  frontend postprocess $MODEL_RESULTS/$test_set-translated.$FROM-$TO $TO v3 > $MODEL_RESULTS/$test_set-translated-detok.$FROM-$TO
  cat $MODEL_RESULTS/$test_set-translated-detok.$FROM-$TO >> $MODEL_RESULTS/combined-translated-detok.$FROM-$TO
  cat $GROUND_TRUTH-$test_set.$TO >> $MODEL_RESULTS/test-combined.$TO
  singularity exec \
    -B $WORKING_DIR:$WORKING_DIR \
    docker://haukurp/moses-smt:1.1.0 \
    /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
    $GROUND_TRUTH-$test_set.$TO < $MODEL_RESULTS/$test_set-translated-detok.$FROM-$TO > $MODEL_RESULTS/$test_set-$FROM-$TO.bleu
done

# Score the combined translations
singularity exec \
  -B $WORKING_DIR:$WORKING_DIR \
  docker://haukurp/moses-smt:1.1.0 \
  /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
  $MODEL_RESULTS/test-combined.$TO < $MODEL_RESULTS/combined-translated-detok.$FROM-$TO > $MODEL_RESULTS/combined-$FROM-$TO.bleu

