#!/bin/bash
#SBATCH --job-name=combined
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=16:10:00
#SBATCH --output=%x-%j.out
#SBATCH --chdir=/home/staff/haukurpj/SMT

WORK_DIR=/work/haukurpj/data
THREADS=$SLURM_CPUS_PER_TASK
# MEMORY=$SLURM_MEM_PER_NODE

# 1=Train truecase IS, 2=Train truecase EN, 3=Process EN mono, 4=Process IS mono, 5=Process train & dev, 6=Create LM data
FIRST_STEP=5
LAST_STEP=6

LANGS="en is"
TRUECASE_MODEL=preprocessing/preprocessing/resources/truecase-model
function train_truecase() {
    LANG=$1
    TRUECASE_DATA="$WORK_DIR"/intermediary/truecase-data."$LANG"
    echo "Created truecase data: $TRUECASE_DATA"
    cat "$WORK_DIR"/intermediary/train-tok."$LANG" "$WORK_DIR"/mono/data-dedup-6578547."$LANG" > "$TRUECASE_DATA"
    sacremoses train-truecase -m "$TRUECASE_MODEL"."$LANG" -j "$THREADS" < "$TRUECASE_DATA"
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
    preprocessing/main.py preprocess "$WORK_DIR"/mono/data-dedup-6578547."$LANG" "$WORK_DIR"/intermediary/lm-data."$LANG" "$LANG" "$TRUECASE_MODEL"."$LANG"
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
            preprocessing/main.py preprocess "$WORK_DIR"/intermediary/"$SPLIT"."$LANG" "$WORK_DIR"/"$SPLIT"/form/data."$LANG" "$LANG" "$TRUECASE_MODEL"."$LANG"
        done
    done
fi

# Create LM-data
if ((FIRST_STEP <= 6 && LAST_STEP >= 6)); then
    for LANG in $LANGS; do
        cat "$WORK_DIR"/train/form/data."$LANG" "$WORK_DIR"/intermediary/lm-data."$LANG" > "$WORK_DIR"/train/form/lm-data."$LANG"
    done
fi