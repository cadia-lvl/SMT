#!/bin/bash
#SBATCH --job-name=combined
#SBATCH --nodes=1
#SBATCH --cpus-per-task=16
#SBATCH --mem=32G
#SBATCH --time=16:10:00
#SBATCH --output=%x-%j.out
#SBATCH --chdir=/home/staff/haukurpj/SMT
# e=fail on pipeline, u=fail on unset var, x=trace commands
set -ex

source environment.sh

# 1=Train truecase EN, 2=Train truecase IS, 3=Process EN mono, 4=Process IS mono, 5=Process train & dev, 6=Create LM data
FIRST_STEP=6
LAST_STEP=6

LANGS="en is"
# TODO: Remove -moses
EXTENSION="-moses"
TRUECASE_MODEL="$TRUECASE_MODEL"$EXTENSION
TRUECASE_DATA="$TRUECASE_DATA"$EXTENSION
function train_truecase() {
    LANG=$1
    echo "Writing truecase data: $TRUECASE_DATA"
    # TODO: Remove tokenizer --moses
    cat "$TRAIN"."$LANG" "$MONO_DETOK"."$LANG" | \
    preprocessing/main.py tokenize - "$TRUECASE_DATA"."$LANG" "$LANG" --tokenizer moses --threads "$THREADS" --batch_size 5000000 --chunksize 10000
    # We just use the truecaser from Moses, sacremoses is not good for this.
    ../mosesdecoder/scripts/recaser/train-truecaser.perl --model "$TRUECASE_MODEL"."$LANG" --corpus "$TRUECASE_DATA"."$LANG"
}

# Train truecase EN
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    train_truecase en
fi

# Train truecase IS
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    train_truecase is
fi

function preprocess_mono() {
    LANG=$1
    # TODO: Remove -moses
    preprocessing/main.py preprocess "$MONO_DETOK"."$LANG" "$MONO_READY""$EXTENSION"."$LANG" "$LANG" --tokenizer moses --truecase_model "$TRUECASE_MODEL"."$LANG" --threads "$THREADS"
}

# Preprocess EN mono
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    preprocess_mono en
fi

# Preprocess IS mono
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
    preprocess_mono is
fi

# Preprocess train & dev
if ((FIRST_STEP <= 5 && LAST_STEP >= 5)); then
    SPLITS="train dev"
    for LANG in $LANGS; do
        for SPLIT in $SPLITS; do
            # TODO: Remove -moses
            preprocessing/main.py preprocess "$DATA_DIR"intermediary/"$SPLIT"."$LANG" "$DATA_DIR""$SPLIT"/form/data"$EXTENSION"."$LANG" "$LANG" --tokenizer moses --truecase_model "$TRUECASE_MODEL"."$LANG" --threads "$THREADS"
        done
    done
fi

# Create LM-data
if ((FIRST_STEP <= 6 && LAST_STEP >= 6)); then
    for LANG in $LANGS; do
        cat "$TRAINING_DATA"$EXTENSION."$LANG" "$MONO_READY"$EXTENSION."$LANG" > "$LM_SURFACE_TRAIN"$EXTENSION."$LANG"
    done
fi