#!/bin/bash
#SBATCH --job-name=preprocess
#SBATCH --nodes=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=16GB
#SBATCH --time=8:10:00
#SBATCH --output=%j-%x.out

WORK_DIR=/work/haukurpj/data/mideind
DIR=/home/staff/haukurpj/SMT/preprocessing
THREADS=$SLURM_CPUS_PER_TASK
# MEMORY=$SLURM_MEM_PER_NODE

FIRST_STEP=7
LAST_STEP=7

# Change the format of the files (useful to keep the same tokenization and enrichment through-out the process)
# TODO: fix
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    for set in "received test-ees test-ema test-opensubtitles"; do
        "$DIR"/main.py p_corpora_to_json "$WORK_DIR"/raw/mideind"$set".en "$WORK_DIR"/"$set".is "$WORK_DIR"/"$set".pickle
    done
fi

# Enrich and tokenize
# TODO: fix paths
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    DATA_SETS="test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        "$DIR"/main.py enrich "$WORK_DIR"/"$set".json "$WORK_DIR"/"$set".enriched.json --chunksize 4000
    done
fi

# Split
# TODO: Fix pickle -> json
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    "$DIR"/main.py split "$WORK_DIR"/enriched.json "$WORK_DIR"/train.enriched.json "$WORK_DIR"/dev.enriched.json
fi

# Train truecase
# TODO: Fix pickle -> json
TRUECASE_PREFIX="$WORK_DIR"/truecase-model
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
    "$DIR"/main.py train-truecase "$WORK_DIR"/train.json "$TRUECASE_PREFIX" --segment form --threads "$THREADS"
    "$DIR"/main.py train-truecase "$WORK_DIR"/train.json "$TRUECASE_PREFIX" --segment lemma --threads "$THREADS"
fi
# These are the outputs
TRUECASE_FORM_EN="$TRUECASE_PREFIX".form.en
TRUECASE_FORM_IS="$TRUECASE_PREFIX".form.is
TRUECASE_LEMMA_EN="$TRUECASE_PREFIX".lemma.en
TRUECASE_LEMMA_IS="$TRUECASE_PREFIX".lemma.is

# Apply truecase to all sets (as this is part of the preprocessing step)
# TODO: Fix pickle -> json
if ((FIRST_STEP <= 5 && LAST_STEP >= 5)); then
    DATA_SETS="dev train test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        "$DIR"/main.py truecase "$WORK_DIR"/"$set".enriched.json --lang en --segment form "$WORK_DIR"/"$set"-true.json "$TRUECASE_FORM_EN"
        "$DIR"/main.py truecase "$WORK_DIR"/"$set"-true.json --lang is --segment form "$WORK_DIR"/"$set"-true.json "$TRUECASE_FORM_IS"
        "$DIR"/main.py truecase "$WORK_DIR"/"$set"-true.json --lang en --segment lemma "$WORK_DIR"/"$set"-true.json "$TRUECASE_LEMMA_EN"
        "$DIR"/main.py truecase "$WORK_DIR"/"$set"-true.json --lang is --segment lemma "$WORK_DIR"/"$set"-true.json "$TRUECASE_LEMMA_IS"
    done
fi

# Write to Moses format for training
# TODO: Fix pickle -> json
if ((FIRST_STEP <= 6 && LAST_STEP >= 6)); then
    DATA_SETS="train dev test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        #TODO: Fix with new paths
        "$DIR"/main.py write "$WORK_DIR"/"$set"-true.json "$WORK_DIR"/"$set" --lemma --pos --form --threads "$THREADS"
    done
fi

# Evaluation and tuning
# TODO: Fix pickle -> json
if ((FIRST_STEP <= 7 && LAST_STEP >= 7)); then
    stage=form
    LANGS="en is"
    # Dev
    set="dev"
    mkdir -p "$WORK_DIR"/dev/"$stage"/
    for lang in $LANGS; do
        "$DIR"/main.py write "$WORK_DIR"/"$set"-true.json "$lang" "$WORK_DIR"/dev/"$stage"/data."$lang" --"$stage" --threads "$THREADS"
    done
    # Test
    mkdir -p "$WORK_DIR"/test/"$stage"/
    DATA_SETS="test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        for lang in $LANGS; do
            "$DIR"/main.py write "$WORK_DIR"/"$set"-true.json "$lang" "$WORK_DIR"/test/"$stage"/data."$lang" --"$stage" --threads "$THREADS"
        done
    done

fi

# Detoknize
if ((FIRST_STEP <= 8 && LAST_STEP >= 8)); then
    DATA_SETS="test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        #TODO: Fix with new paths
        "$DIR"/main.py detokenize "$WORK_DIR"/"$set"."$stage".en "$WORK_DIR"/"$set"."$stage".detok.en en
        "$DIR"/main.py detokenize "$WORK_DIR"/"$set"."$stage".is "$WORK_DIR"/"$set"."$stage".detok.is is
    done
fi