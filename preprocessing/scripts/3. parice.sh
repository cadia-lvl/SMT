#!/bin/bash
#SBATCH --job-name=parice
#SBATCH --nodes=1
#SBATCH --cpus-per-task=6
#SBATCH --mem=16GB
#SBATCH --time=8:10:00
#SBATCH --output=%x-%j.out
#SBATCH --chdir=/home/staff/haukurpj/SMT

WORK_DIR=/work/haukurpj/data
THREADS=$SLURM_CPUS_PER_TASK
# MEMORY=$SLURM_MEM_PER_NODE

FIRST_STEP=2
LAST_STEP=2

LANGS="en is"
function show_file() {
    wc -l $1
    head -n 2 $1
}

# Split
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    for LANG in $LANGS; do
        preprocessing/main.py split "$WORK_DIR"/raw/mideind/train."$LANG" $WORK_DIR/intermediary/train."$LANG" $WORK_DIR/intermediary/dev."$LANG" 
        show_file $WORK_DIR/intermediary/train."$LANG"
    done
fi

# Tokenize
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    for LANG in $LANGS; do
        preprocessing/main.py tokenize "$WORK_DIR"/intermediary/train."$LANG" $WORK_DIR/intermediary/train-tok."$LANG" "$LANG" --threads "$THREADS"
        show_file $WORK_DIR/intermediary/train-tok."$LANG"
    done
fi
