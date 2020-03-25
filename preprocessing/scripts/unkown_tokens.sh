#!/bin/bash
WORK_DIR=/work/haukurpj/data
LANG=is

FIRST_STEP=3
LAST_STEP=3

if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    preprocessing/main.py extract-known-tokens "$WORK_DIR"/train/form/data.is "$WORK_DIR"/train/form/tok.is
    wc -l "$WORK_DIR"/train/form/tok.is
fi
TEST_SETS="ees ema opensubtitles"
TRUECASE_MODEL=preprocessing/preprocessing/resources/truecase-model."$LANG"

# Find unknowns
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    for set in $TEST_SETS; do
        preprocessing/main.py preprocess $WORK_DIR/test/raw/"$set".$LANG - $LANG $TRUECASE_MODEL  | preprocessing/main.py unknown-tokens - /work/haukurpj/data/train/form/tok.is "$set"-unknown.is
        wc -l "$set"-unknown.is
    done
    cat {ees,ema,opensubtitles}-unknown.is | sort | uniq > unknown.is
    wc -l unknown.is
fi

function split_unkowns() {
    IN=$1
    OUT=$2
    echo "$IN: Total unknown tokens $(wc -l $IN)"
    echo "Running Kvistur"
    python kvistur/kvistur.py $IN $IN-kvistur
    echo "Found composite tokens: $(grep -c _ $IN-kvistur), non-comp=total-composite"
    sed 's/_/\n/' $IN-kvistur > $IN-kvistur-split.is
    preprocessing/main.py unknown-tokens $IN-kvistur-split.is /work/haukurpj/data/train/form/tok.is $OUT
    echo "$OUT: Total unknown tokens $(wc -l $OUT)"
}

if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    split_unkowns unknown.is 1-split-unknown.is
    split_unkowns 1-split-unknown.is 2-split-unknown.is
    split_unkowns 2-split-unknown.is 3-split-unknown.is
fi