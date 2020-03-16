#!/bin/bash
#SBATCH --job-name=preprocess
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=32G
#SBATCH --time=16:10:00
#SBATCH --output=%x-%j.out

WORK_DIR=/work/haukurpj/data
DIR=/home/staff/haukurpj/SMT/preprocessing
THREADS=$SLURM_CPUS_PER_TASK
# MEMORY=$SLURM_MEM_PER_NODE

# 1=Read directory and map to serialization format
FIRST_STEP=3
LAST_STEP=3

if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    TARGET_DIR="$WORK_DIR"mono/
    mkdir -p "$TARGET_DIR"
    "$DIR"/main.py read-rmh "$WORK_DIR"raw/risamalheild "$TARGET_DIR"data.is --threads "$THREADS" --chunksize 200
fi

if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    TARGET_DIR="$WORK_DIR"mono/
    mkdir -p "$TARGET_DIR"
    "$DIR"/main.py deduplicate "$TARGET_DIR"data.is "$TARGET_DIR"data-dedup.is
fi

# Train truecase
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    TARGET_DIR="$WORK_DIR"mono/
    mkdir -p "$TARGET_DIR"
    cat "$WORK_DIR"/train/form/data.is "$WORK_DIR"/mono/data-dedup.is | preprocessing/main.py train-truecase - "$WORK_DIR"/train/truecase-model.form.is is --threads "$THREADS"
fi

# Truecase
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
    TARGET_DIR="$WORK_DIR"mono/
    mkdir -p "$TARGET_DIR"
    "$DIR"/main.py truecase "$TARGET_DIR"data-dedup.is "$TARGET_DIR"data-true.is "$WORK_DIR"/train/truecase-model.form.is
fi