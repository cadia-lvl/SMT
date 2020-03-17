#!/bin/bash
#SBATCH --job-name=preprocess
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=64G
#SBATCH --time=16:10:00
#SBATCH --output=%x-%j.out
#SBATCH --chdir=/home/staff/haukurpj/SMT

WORK_DIR=/work/haukurpj/data/
THREADS=10
#THREADS=$SLURM_CPUS_PER_TASK
# MEMORY=$SLURM_MEM_PER_NODE

# 1=Read RMH
FIRST_STEP=5
LAST_STEP=5

TARGET_DIR="$WORK_DIR"mono/
mkdir -p "$TARGET_DIR"

if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    preprocessing/main.py read-rmh "$WORK_DIR"raw/risamalheild "$TARGET_DIR"data.is --threads "$THREADS" --chunksize 200
fi

if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    preprocessing/main.py deduplicate "$TARGET_DIR"data.is "$TARGET_DIR"data-dedup.is
fi

# Shrink RMH - shuffle and sample 1/10 of the data
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    wc -l "$TARGET_DIR"data-dedup.is # =65785474
    shuf "$TARGET_DIR"data-dedup.is | head -n 6578547 > "$TARGET_DIR"data-dedup-6578547.is
    echo "Done!"
fi

# Train truecase
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
    LM_DATA="$WORK_DIR"/train/form/data-lm.is
    cat "$WORK_DIR"/train/form/data.is "$TARGET_DIR"data-dedup-6578547.is > "$LM_DATA"
    sacremoses train-truecase -m "$WORK_DIR"/train/truecase-model.form.is -j "$THREADS" < "$LM_DATA"
fi

# Truecase
if ((FIRST_STEP <= 5 && LAST_STEP >= 5)); then
    preprocessing/main.py truecase "$TARGET_DIR"data-dedup-6578547.is "$TARGET_DIR"data-dedup-6578547-true.is "$WORK_DIR"/train/truecase-model.form.is
fi