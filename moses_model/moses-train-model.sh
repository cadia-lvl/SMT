#!/bin/bash
#SBATCH --job-name=train-moses
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=16GB
#SBATCH --time=6:00:00
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

MOSES_TAG="1.1.0"
DATA_DIR="${WORK_DIR}/process"
MOSESDECODER="/opt/moses"
MOSESDECODER_TOOLS="/opt/moses_tools"

LANG_FROM="is"
LANG_TO="en"
MODIFIER="tokenization"
TRAINING_DATA="${DATA_DIR}/parice-train-processed-tok_low"
VALIDATION_DATA="${DATA_DIR}/parice-val-final-tok_low"
TEST_DATA="${DATA_DIR}/parice-test-final-tok_low"
# Set LM_EXTRA_DATA to "" if no extra lm data.
# LM_EXTRA_DATA="${DATA_DIR}/rmh-final.is"
# LM_EXTRA_DATA="${DATA_DIR}/mono-final.en"
LM_EXTRA_DATA=""

CLEAN_MIN_LENGTH=1
CLEAN_MAX_LENGTH=70
LM_ORDER=3

MODEL_NAME="${LANG_FROM}-${LANG_TO}-${MODIFIER}"
CLEAN_DATA="${DATA_DIR}/${MODEL_NAME}-train"
LM="${DATA_DIR}/${MODEL_NAME}.${LANG_TO}.blm"

function run_in_singularity() {
  singularity exec \
  -B $WORK_DIR:$WORK_DIR \
	docker://haukurp/moses-smt:$MOSES_TAG \
  "$@"
}
# Test if data is there
function check_data() {
  if [ ! -f $1 ]; then
    echo "File does not exist. Exiting..."
    exit 1
  fi
}
check_data $TRAINING_DATA.en
check_data $TRAINING_DATA.is
check_data $VALIDATION_DATA.en
check_data $VALIDATION_DATA.is
check_data $TEST_DATA.en
check_data $TEST_DATA.is

# Data prep
run_in_singularity ${MOSESDECODER}/scripts/training/clean-corpus-n.perl $TRAINING_DATA $LANG_FROM $LANG_TO $CLEAN_DATA $CLEAN_MIN_LENGTH $CLEAN_MAX_LENGTH

# LM creation
LM_DATA=${DATA_DIR}/${MODEL_NAME}-lm.${LANG_TO}
cat ${CLEAN_DATA}.${LANG_TO} $LM_EXTRA_DATA > $LM_DATA
run_in_singularity ${MOSESDECODER}/bin/lmplz --order $LM_ORDER --temp_prefix $DATA_DIR/ --memory 50% --discount_fallback < ${LM_DATA} > ${LM}.arpa
run_in_singularity ${MOSESDECODER}/bin/build_binary -S 50% ${LM}.arpa ${LM}

# Training
MODEL_DIR="${WORK_DIR}/${MODEL_NAME}"
mkdir -p ${MODEL_DIR}
BASE_DIR="${MODEL_DIR}/base"
mkdir -p ${BASE_DIR}
run_in_singularity ${MOSESDECODER}/scripts/training/train-model.perl -root-dir $BASE_DIR \
        -corpus $CLEAN_DATA \
        -f $LANG_FROM \
        -e $LANG_TO \
        -alignment grow-diag-final-and -reordering msd-bidirectional-fe \
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
BINARISE_DIR="${MODEL_DIR}/binarised"
mkdir -p ${BINARISE_DIR}
BINARISED_MOSES_INI="${BINARISE_DIR}/moses.ini"
BINARISED_PHRASE_TABLE="${BINARISE_DIR}/phrase-table"
BINARISED_REORDERING_TABLE="${BINARISE_DIR}/reordering-table"
BINARISED_LM="$BINARISE_DIR/lm.blm"

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

# Translate the test data
run_in_singularity ${MOSESDECODER}/bin/moses \
        -f $BINARISED_MOSES_INI < $TEST_DATA.$LANG_FROM > ${BINARISE_DIR}/translated.$LANG_FROM

# Score the translation
run_in_singularity ${MOSESDECODER}/scripts/generic/multi-bleu.perl -lc $TEST_DATA.$LANG_TO < ${BINARISE_DIR}/translated.$LANG_FROM > ${BINARISE_DIR}/translated.bleu
