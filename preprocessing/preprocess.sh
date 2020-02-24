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

# Change the format of the files (useful to keep the same tokenization through-out the process)
# for set in "received test-ees test-ema test-opensubtitles"; do
#     python "$DIR"/main.py read_p_corpora_to_pickle "$WORK_DIR"/$set.en "$WORK_DIR"/$set.is "$WORK_DIR"/$set.pickle

# Enrich and tokenize
# DATA_SETS="test-ees test-ema test-opensubtitles"
# for set in $DATA_SETS; do
#     python "$DIR"/main.py enrich "$WORK_DIR"/"$set".pickle "$WORK_DIR"/"$set".enriched.pickle --chunksize 4000
# done
# Split
# python "$DIR"/main.py split "$WORK_DIR"/enriched.pickle "$WORK_DIR"/train.enriched.pickle "$WORK_DIR"/dev.enriched.pickle

# Train truecase
TRUECASE_PREFIX="$WORK_DIR"/truecase-model
# python "$DIR"/main.py train-truecase "$WORK_DIR"/train.pickle "$TRUECASE_PREFIX" --segment form --threads "$THREADS"
# python "$DIR"/main.py train-truecase "$WORK_DIR"/train.pickle "$TRUECASE_PREFIX" --segment lemma --threads "$THREADS"
# These are the outputs
TRUECASE_FORM_EN="$TRUECASE_PREFIX".form.en
TRUECASE_FORM_IS="$TRUECASE_PREFIX".form.is
TRUECASE_LEMMA_EN="$TRUECASE_PREFIX".lemma.en
TRUECASE_LEMMA_IS="$TRUECASE_PREFIX".lemma.is

# Apply truecase to all sets (as this is part of the preprocessing step)
DATA_SETS="test-ees test-ema test-opensubtitles"
for set in $DATA_SETS; do
    python "$DIR"/main.py truecase "$WORK_DIR"/"$set".enriched.pickle --lang en --segment form "$WORK_DIR"/"$set"-true.pickle "$TRUECASE_FORM_EN"
    python "$DIR"/main.py truecase "$WORK_DIR"/"$set"-true.pickle --lang is --segment form "$WORK_DIR"/"$set"-true.pickle "$TRUECASE_FORM_IS"
    python "$DIR"/main.py truecase "$WORK_DIR"/"$set"-true.pickle --lang en --segment lemma "$WORK_DIR"/"$set"-true.pickle "$TRUECASE_LEMMA_EN"
    python "$DIR"/main.py truecase "$WORK_DIR"/"$set"-true.pickle --lang is --segment lemma "$WORK_DIR"/"$set"-true.pickle "$TRUECASE_LEMMA_IS"
done

# Write to Moses format and LM training. 