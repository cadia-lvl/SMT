#!/bin/bash
#SBATCH --job-name=en-mono
#SBATCH --nodes=1
#SBATCH --cpus-per-task=30
#SBATCH --mem=64G
#SBATCH --time=16:10:00
#SBATCH --output=%x-%j.out
#SBATCH --chdir=/home/staff/haukurpj/SMT

WORK_DIR=/work/haukurpj/data/
THREADS=$SLURM_CPUS_PER_TASK
# MEMORY=$SLURM_MEM_PER_NODE

# 1=Read RMH
FIRST_STEP=3
LAST_STEP=6

TARGET_DIR="$WORK_DIR"mono/
mkdir -p "$TARGET_DIR"

# Remove lines which are too long
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    sed '/^.\{1024\}./d' <"$TARGET_DIR"data.en> "$TARGET_DIR"data-short.en
fi

if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    preprocessing/main.py tokenize "$TARGET_DIR"data-short.en "$TARGET_DIR"data-tok.en en --threads "$THREADS" --batch_size 5000000 --chunksize 10000
fi

if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    preprocessing/main.py deduplicate "$TARGET_DIR"data-tok.en "$TARGET_DIR"data-dedup.en
fi

# Shrink RMH - shuffle and sample 1/10 of the data
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
    wc -l "$TARGET_DIR"data-dedup.en # =65785474
    shuf "$TARGET_DIR"data-dedup.en | head -n 6578547 > "$TARGET_DIR"data-dedup-6578547.en
    echo "Done!"
fi

# Train truecase
if ((FIRST_STEP <= 5 && LAST_STEP >= 5)); then
    LM_DATA="$WORK_DIR"/train/form/data-lm.en
    cat "$WORK_DIR"/train/form/data.en "$TARGET_DIR"data-dedup-6578547.en > "$LM_DATA"
    sacremoses train-truecase -m "$WORK_DIR"/train/truecase-model.form.en -j "$THREADS" < "$LM_DATA"
fi

# Truecase
if ((FIRST_STEP <= 6 && LAST_STEP >= 6)); then
    preprocessing/main.py truecase "$TARGET_DIR"data-dedup-6578547.en "$TARGET_DIR"data-dedup-6578547-true.en "$WORK_DIR"/train/truecase-model.form.en
fi