#!/bin/bash
#SBATCH --job-name=moses-e2e
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --chdir=/home/staff/haukurpj/SMT
#SBATCH --time=18:01:00
#SBATCH --output=%x-%j.out
# e=fail on pipeline, u=fail on unset var, x=trace commands
set -ex

# We assume that the script is run from the base repo directory
# Use environment
source ./scripts/environment.sh

# 1=Format, 2=Preprocess, 3=Train, 4=Package
FIRST_STEP=2
LAST_STEP=2

TEST_SETS="ees ema opensubtitles"

mkdir -p "$MODEL_DIR"

# Format
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
            cp "$RAW_DIR"/parice/parice_test_set_filtered/filtered/"$LANG"/"$TEST"."$LANG" "$FORMATTED_DIR"/parice/"$TEST"."$LANG"
        done
    done
fi

# Preprocess
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    mkdir -p "$OUT_DIR"
    
    function train_truecase() {
        LANG=$1
        cat "$OUT_DIR"/train+dict."$LANG" "$FORMATTED_DIR"/mono/data-short."$LANG" | \
        preprocessing/main.py tokenize - "$OUT_DIR"/truecase-data."$LANG" "$LANG" --threads "$THREADS" --batch_size 5000000 --chunksize 10000
        # We just use the truecaser from Moses, sacremoses is not good for this.
        "$MOSESDECODER"/scripts/recaser/train-truecaser.perl --model "$TRUECASE_MODEL"."$LANG" --corpus "$OUT_DIR"/truecase-data."$LANG"
    }
    
    for LANG in $LANGS; do
        # Add the dictionary data to the training data
        cat "$FORMATTED_DIR"/parice/train."$LANG" "$FORMATTED_DIR"/dictionary/*."$LANG" > "$OUT_DIR"/train+dict."$LANG"
        train_truecase $LANG
        preprocessing/main.py preprocess "$FORMATTED_DIR"/mono/data-short."$LANG" "$OUT_DIR"/mono."$LANG" "$LANG" --truecase_model "$TRUECASE_MODEL"."$LANG" --threads "$THREADS" --batch_size 5000000 --chunksize 10000
        preprocessing/main.py preprocess "$OUT_DIR"/train+dict."$LANG" "$OUT_DIR"/para-train."$LANG" "$LANG" --truecase_model "$TRUECASE_MODEL"."$LANG" --threads "$THREADS" --batch_size 5000000 --chunksize 10000
        preprocessing/main.py preprocess "$FORMATTED_DIR"/parice/dev."$LANG" "$OUT_DIR"/para-dev."$LANG" "$LANG" --truecase_model "$TRUECASE_MODEL"."$LANG" --threads "$THREADS" --batch_size 5000000 --chunksize 10000
        cat "$OUT_DIR"/para-train."$LANG" "$OUT_DIR"/mono."$LANG" > "$OUT_DIR"/lm-data."$LANG"
        bash scripts/run_in_singularity.sh scripts/2preprocess/lm.sh is "$OUT_DIR"/lm-data."$LANG" "$LM_MODEL" 5 
    done
fi
# Train
# Package (Moses and Python)