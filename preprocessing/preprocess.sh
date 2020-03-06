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

# Change the format of the files (useful to keep the same tokenization through-out the process)
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    for set in "received test-ees test-ema test-opensubtitles"; do
        python "$DIR"/main.py read_p_corpora_to_pickle "$WORK_DIR"/"$set".en "$WORK_DIR"/"$set".is "$WORK_DIR"/"$set".pickle
    done
fi

# Enrich and tokenize
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    DATA_SETS="test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        python "$DIR"/main.py enrich "$WORK_DIR"/"$set".pickle "$WORK_DIR"/"$set".enriched.pickle --chunksize 4000
    done
fi

# Split
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    python "$DIR"/main.py split "$WORK_DIR"/enriched.pickle "$WORK_DIR"/train.enriched.pickle "$WORK_DIR"/dev.enriched.pickle
fi

# Train truecase
TRUECASE_PREFIX="$WORK_DIR"/truecase-model
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
    python "$DIR"/main.py train-truecase "$WORK_DIR"/train.pickle "$TRUECASE_PREFIX" --segment form --threads "$THREADS"
    python "$DIR"/main.py train-truecase "$WORK_DIR"/train.pickle "$TRUECASE_PREFIX" --segment lemma --threads "$THREADS"
fi
# These are the outputs
TRUECASE_FORM_EN="$TRUECASE_PREFIX".form.en
TRUECASE_FORM_IS="$TRUECASE_PREFIX".form.is
TRUECASE_LEMMA_EN="$TRUECASE_PREFIX".lemma.en
TRUECASE_LEMMA_IS="$TRUECASE_PREFIX".lemma.is

# Apply truecase to all sets (as this is part of the preprocessing step)
if ((FIRST_STEP <= 5 && LAST_STEP >= 5)); then
    DATA_SETS="dev train test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        python "$DIR"/main.py truecase "$WORK_DIR"/"$set".enriched.pickle --lang en --segment form "$WORK_DIR"/"$set"-true.pickle "$TRUECASE_FORM_EN"
        python "$DIR"/main.py truecase "$WORK_DIR"/"$set"-true.pickle --lang is --segment form "$WORK_DIR"/"$set"-true.pickle "$TRUECASE_FORM_IS"
        python "$DIR"/main.py truecase "$WORK_DIR"/"$set"-true.pickle --lang en --segment lemma "$WORK_DIR"/"$set"-true.pickle "$TRUECASE_LEMMA_EN"
        python "$DIR"/main.py truecase "$WORK_DIR"/"$set"-true.pickle --lang is --segment lemma "$WORK_DIR"/"$set"-true.pickle "$TRUECASE_LEMMA_IS"
    done
fi

# Write to Moses format for training
if ((FIRST_STEP <= 6 && LAST_STEP >= 6)); then
    DATA_SETS="train dev test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        #TODO: Fix with new paths
        python "$DIR"/main.py write "$WORK_DIR"/"$set"-true.pickle "$WORK_DIR"/"$set" --lemma --pos --form --threads "$THREADS"
    done
fi

# Evaluation and tuning
if ((FIRST_STEP <= 7 && LAST_STEP >= 7)); then
    stage=form
    LANGS="en is"
    # Dev
    set="dev"
    mkdir -p "$WORK_DIR"/dev/"$stage"/
    for lang in $LANGS; do
        python "$DIR"/main.py write "$WORK_DIR"/"$set"-true.pickle "$lang" "$WORK_DIR"/dev/"$stage"/data."$lang" --"$stage" --threads "$THREADS"
    done
    # Test
    mkdir -p "$WORK_DIR"/test/"$stage"/
    DATA_SETS="test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        for lang in $LANGS; do
            python "$DIR"/main.py write "$WORK_DIR"/"$set"-true.pickle "$lang" "$WORK_DIR"/test/"$stage"/data."$lang" --"$stage" --threads "$THREADS"
        done
    done

fi

# Detoknize
if ((FIRST_STEP <= 8 && LAST_STEP >= 8)); then
    DATA_SETS="test-ees test-ema test-opensubtitles"
    for set in $DATA_SETS; do
        #TODO: Fix with new paths
        python "$DIR"/main.py detokenize "$WORK_DIR"/"$set"."$stage".en "$WORK_DIR"/"$set"."$stage".detok.en en
        python "$DIR"/main.py detokenize "$WORK_DIR"/"$set"."$stage".is "$WORK_DIR"/"$set"."$stage".detok.is is
    done
fi