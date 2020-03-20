#!/bin/bash
#SBATCH --job-name=translate
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=8GB
#SBATCH --time=4:00:00
#SBATCH --output=%x-%j.out
#SBATCH --chdir=/home/staff/haukurpj/SMT

WORK_DIR=/work/haukurpj/data/

FIRST_STEP=5
LAST_STEP=5

if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    mkdir translated
    LANG_FROM="en"
    LANG_TO="is"
    for set in "ees ema opensubtitles"; do
        preprocessing/main.py translate "$WORK_DIR"test/raw/"$set"."$LANG_FROM" translated/"$set"."$LANG_FROM"-"$LANG_TO" "$LANG_FROM" "$LANG_TO"
    done
    LANG_FROM="is"
    LANG_TO="en"
    for set in "ees ema opensubtitles"; do
        preprocessing/main.py translate "$WORK_DIR"test/raw/"$set"."$LANG_FROM" translated/"$set"."$LANG_FROM"-"$LANG_TO" "$LANG_FROM" "$LANG_TO"
    done
fi

if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    preprocessing/main.py deduplicate "$TARGET_DIR"data.is "$TARGET_DIR"data-dedup.is
fi
