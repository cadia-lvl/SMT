#!/bin/bash
#SBATCH --job-name=preprocess
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=32G
#SBATCH --time=16:10:00
#SBATCH --output=%x-%j.out

WORK_DIR=/work/haukurpj/data/
DIR=/home/staff/haukurpj/SMT/preprocessing
THREADS=$SLURM_CPUS_PER_TASK
# MEMORY=$SLURM_MEM_PER_NODE

# 1=Read directory and map to serialization format
FIRST_STEP=1
LAST_STEP=2

if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    TARGET_DIR="$WORK_DIR"mono/
    mkdir -p "$TARGET_DIR"
    python "$DIR"/main.py read-rmh "$WORK_DIR"raw/risamalheild "$TARGET_DIR"rmh.json --threads "$THREADS" --chunksize 200
fi

if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    TARGET_DIR="$WORK_DIR"mono/
    mkdir -p "$TARGET_DIR"
    python "$DIR"/main.py deduplicate $(ls "$TARGET_DIR"rmh.json*) "$TARGET_DIR"rmh-dedup.json
fi