#!/bin/bash
#SBATCH --job-name=mono-en
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=16G
#SBATCH --time=16:10:00
#SBATCH --output=%x-%j.out
#SBATCH --chdir=/home/staff/haukurpj/SMT

WORK_DIR=/work/haukurpj/data/
THREADS=$SLURM_CPUS_PER_TASK
# MEMORY=$SLURM_MEM_PER_NODE

# 1=Clean, 2=Tokenize, 3=Deduplicate, 4=Shrink
FIRST_STEP=1
LAST_STEP=4

TARGET_DIR="$WORK_DIR"mono/
mkdir -p "$TARGET_DIR"

# Remove lines which are too long
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    sed '/^.\{1024\}./d' <"$TARGET_DIR"data.en> "$TARGET_DIR"data-short.en
fi

# Tokenize
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    preprocessing/main.py tokenize "$TARGET_DIR"data-short.en "$TARGET_DIR"data-tok.en en --threads "$THREADS" --batch_size 5000000 --chunksize 10000
fi

# Deduplicate
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    preprocessing/main.py deduplicate "$TARGET_DIR"data-tok.en "$TARGET_DIR"data-dedup.en
fi

# Shrink 
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
    wc -l "$TARGET_DIR"data-dedup.en # =65785474
    shuf "$TARGET_DIR"data-dedup.en | head -n 6578547 > "$TARGET_DIR"data-dedup-6578547.en
    echo "Done!"
fi
