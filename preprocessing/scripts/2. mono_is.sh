#!/bin/bash
#SBATCH --job-name=mono-is
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=64G
#SBATCH --time=16:10:00
#SBATCH --output=%x-%j.out
#SBATCH --chdir=/home/staff/haukurpj/SMT
# e=fail on pipeline, u=fail on unset var, x=trace commands
set -ex

source environment.sh

# 1=Read RMH, 2=Dedup, 3=Shrink, 4=Detokenize
FIRST_STEP=2
LAST_STEP=4

TARGET_DIR="$WORK_DIR"mono/
mkdir -p "$TARGET_DIR"

# Read RMH
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    preprocessing/main.py read-rmh "$WORK_DIR"raw/risamalheild "$TARGET_DIR"data.is --threads "$THREADS" --chunksize 200
fi

# Deduplicate
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    preprocessing/main.py deduplicate "$TARGET_DIR"data.is "$TARGET_DIR"data-dedup.is
fi

# Shrink RMH - shuffle and sample 1/10 of the data
if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    wc -l "$TARGET_DIR"data-dedup.is # =65785474
    shuf "$TARGET_DIR"data-dedup.is | head -n 6578547 > "$TARGET_DIR"data-dedup-6578547.is
    echo "Done!"
fi

# Detok - for tokenization experiments 
if ((FIRST_STEP <= 4 && LAST_STEP >= 4)); then
    echo "Detokenizing"
    preprocessing/main.py detokenize "$TARGET_DIR"data-dedup-6578547.is "$TARGET_DIR"data-dedup-6578547-detok.is is
    echo "Done!"
fi