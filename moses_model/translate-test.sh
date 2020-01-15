#!/bin/bash
#SBATCH --job-name=translate-test.sh
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=16GB
#SBATCH --time=1:00:00

MODEL_NAME=new-test
FROM=en
TO=is
MODEL=$FROM-$TO-$MODEL_NAME
WORKING_DIR=/work/haukurpj

export THREADS=$SLURM_CPUS_PER_TASK
TEST_SETS="ees ema opensubtitles"

# Test if data is there
function check_data() {
  if [ ! -f $1 ]; then
    echo "File does not exist. Exiting..."
    exit 1
  fi
}
for test_set in $TEST_SETS; do
  check_data $WORKING_DIR/$test_set-lower.$TO
  check_data $WORKING_DIR/$test_set-processed.$FROM
done

# Remove the combined files if exist.
rm combined-lower.$TO || true
rm combined-translated-detok.$FROM-$TO || true

# Translate, post process and evaluate the test sets one by one.
for test_set in $TEST_SETS; do
  cat $WORKING_DIR/$test_set-lower.$TO >> $WORKING_DIR/combined-lower.$TO
  singularity run \
    -B $WORKING_DIR:$WORKING_DIR \
     docker://haukurp/moses-smt:1.1.0 \
     /opt/moses/bin/moses -f $WORKING_DIR/$MODEL/binarised/moses.ini \
     -threads $THREADS \
      < $WORKING_DIR/$test_set-processed.$FROM \
      > $WORKING_DIR/$test_set-translated.$FROM-$TO

  frontend postprocess $WORKING_DIR/$test_set-translated.$FROM-$TO $TO v3 > $WORKING_DIR/$test_set-translated-detok.$FROM-$TO
  cat $WORKING_DIR/$test_set-translated-detok.$FROM-$TO >> $WORKING_DIR/combined-translated-detok.$FROM-$TO
  singularity exec \
    -B $WORKING_DIR:$WORKING_DIR \
    docker://haukurp/moses-smt:1.1.0 \
    /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
    $WORKING_DIR/$test_set-lower.$TO < $WORKING_DIR/$test_set-translated-detok.$FROM-$TO > $WORKING_DIR/$test_set-$FROM-$TO.bleu

done
singularity exec \
  -B $WORKING_DIR:$WORKING_DIR \
  docker://haukurp/moses-smt:1.1.0 \
  /opt/moses/scripts/generic/multi-bleu-detok.perl -lc \
  $WORKING_DIR/combined-lower.$TO < $WORKING_DIR/combined-translated-detok.$FROM-$TO > $WORKING_DIR/combined-$FROM-$TO.bleu

