#!/bin/bash
#SBATCH --job-name=moses-e2e
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --chdir=/home/staff/haukurpj/SMT
#SBATCH --time=18:01:00
#SBATCH --output=logs/%x-%j.out
# e=fail on pipeline, u=fail on unset var, x=trace commands
set -ex

# We assume that the script is run from the base repo directory

# 1=Format, 2=Preprocess, 3=Train, 4=Package
FIRST_STEP=4
LAST_STEP=4

source scripts/environment.sh

# Format -> FORMATTED_DIR
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    mkdir -p "$FORMATTED_DIR"
    
    # Dictonaries
    mkdir -p "$FORMATTED_DIR"/dictionary
    scripts/1format/extract_dicts.sh "$RAW_DIR"/dictionary "$FORMATTED_DIR"/dictionary

    # EN mono
    mkdir -p "$FORMATTED_DIR"/mono
    scripts/1format/en_mono_format.py "$RAW_DIR"/mono "$FORMATTED_DIR"/mono
    # Remove lines which are too long, tokenize, deduplicate, shorten, detokenize
    sed '/^.\{1024\}./d' <"$FORMATTED_DIR"/mono/data.en | \
    preprocessing/main.py tokenize - - en --threads "$THREADS" --batch_size 5000000 --chunksize 10000 | \
    preprocessing/main.py deduplicate - - | \
    shuf | head -n 6578547 | \
    preprocessing/main.py detokenize - "$FORMATTED_DIR"/mono/data-short.en en

    # RMH
    # The data is already tokenized so we deduplicate, shorten, detokenize
    preprocessing/main.py read-rmh "$RAW_DIR"/rmh "$FORMATTED_DIR"/mono/data.is --threads "$THREADS" --chunksize 500
    preprocessing/main.py deduplicate "$FORMATTED_DIR"/mono/data.is - | \
    shuf | head -n 6578547 | \
    preprocessing/main.py detokenize - "$FORMATTED_DIR"/mono/data-short.is is

    # Parice
    mkdir -p "$FORMATTED_DIR"/parice
    # Split
    for LANG in $LANGS; do
        preprocessing/main.py split "$RAW_DIR"/parice/train."$LANG" "$FORMATTED_DIR"/parice/train."$LANG" "$FORMATTED_DIR"/parice/dev."$LANG" 
        for TEST in $TEST_SETS; do
            cp "$RAW_DIR"/parice/parice_test_set_filtered/filtered/"$LANG"/"$TEST"."$LANG" "$FORMATTED_DIR"/parice/test-"$TEST"."$LANG"
        done
    done
fi

# Preprocess -> OUT_DIR
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    mkdir -p "$OUT_DIR"
    mkdir -p "$OUT_DIR"/train 
    mkdir -p "$OUT_DIR"/dev
    mkdir -p "$OUT_DIR"/test 
    for LANG in $LANGS; do
        sbatch --wait scripts/2preprocess/preprocess.sh "$LANG" &
    done
    wait
fi
# Train & eval -> MODEL_DIR
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    mkdir -p "$MODEL_DIR"
    rm -r "$EN_IS_DIR" || true
    rm -r "$IS_EN_DIR" || true
    mkdir -p "$EN_IS_DIR"
    mkdir -p "$IS_EN_DIR"
    mkdir -p "$MODEL_RESULTS_DIR"
    sbatch --wait scripts/run_in_singularity.sh scripts/3train/dict.sh en is "$EN_IS_DIR" &
    sbatch --wait scripts/run_in_singularity.sh scripts/3train/dict.sh is en "$IS_EN_DIR" &
    wait
    rm "$MODEL_RESULTS_DIR"/combined-translated-post.* || true
    for TEST in $TEST_SETS; do
        # Translate
        sbatch --wait scripts/run_in_singularity.sh scripts/3train/translate.sh \
                "$EN_IS_DIR"/binarised/moses.ini \
                "$TEST_DIR"/"$TEST"-processed.en \
                "$MODEL_RESULTS_DIR"/"$TEST"-translated.en-is &
        sbatch --wait scripts/run_in_singularity.sh scripts/3train/translate.sh \
                "$IS_EN_DIR"/binarised/moses.ini \
                "$TEST_DIR"/"$TEST"-processed.is \
                "$MODEL_RESULTS_DIR"/"$TEST"-translated.is-en &
        wait
        preprocessing/main.py postprocess "$MODEL_RESULTS_DIR"/"$TEST"-translated.is-en "$MODEL_RESULTS_DIR"/"$TEST"-translated-post.is-en en
        preprocessing/main.py postprocess "$MODEL_RESULTS_DIR"/"$TEST"-translated.en-is "$MODEL_RESULTS_DIR"/"$TEST"-translated-post.en-is is
        
        cat "$MODEL_RESULTS_DIR"/"$TEST"-translated-post.is-en >> "$MODEL_RESULTS_DIR"/combined-translated-post.is-en
        cat "$MODEL_RESULTS_DIR"/"$TEST"-translated-post.en-is >> "$MODEL_RESULTS_DIR"/combined-translated-post.en-is
        # Evaluate
        sbatch --wait scripts/run_in_singularity.sh scripts/3train/evaluate.sh \
                "$MODEL_RESULTS_DIR"/"$TEST"-translated-post.en-is \
                "$TEST_DIR"/"$TEST".is \
                "$MODEL_RESULTS_DIR"/"$TEST".en-is.bleu &
        sbatch --wait scripts/run_in_singularity.sh scripts/3train/evaluate.sh \
                "$MODEL_RESULTS_DIR"/"$TEST"-translated-post.is-en \
                "$TEST_DIR"/"$TEST".en \
                "$MODEL_RESULTS_DIR"/"$TEST".is-en.bleu &
        wait
    done
    sbatch --wait scripts/run_in_singularity.sh scripts/3train/evaluate.sh \
            "$MODEL_RESULTS_DIR"/combined-translated-post.is-en \
            "$TEST_DIR"/combined.en \
            "$MODEL_RESULTS_DIR"/combined.is-en.bleu &
    sbatch --wait scripts/run_in_singularity.sh scripts/3train/evaluate.sh \
            "$MODEL_RESULTS_DIR"/combined-translated-post.en-is \
            "$TEST_DIR"/combined.is \
            "$MODEL_RESULTS_DIR"/combined.en-is.bleu &
    wait
fi

# Package (Moses and Python) - cannot be run on the cluster
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
    bash preprocessing/docker-build.sh 3.2.0
    bash scripts/4package/docker-build.sh haukurpj@torpaq:/home/staff/haukurpj/SMT/model/en-is/binarised haukurp/moses-smt:en-is
    bash scripts/4package/docker-build.sh haukurpj@torpaq:/home/staff/haukurpj/SMT/model/is-en/binarised haukurp/moses-smt:is-en
fi