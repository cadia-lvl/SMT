#!/bin/bash
# check if script is started via SLURM or bash
# if with SLURM: there variable '$SLURM_JOB_ID' will exist
if [ -n "$SLURM_JOB_ID" ];  then
    export THREADS="$SLURM_CPUS_PER_TASK"
    export MEMORY="$SLURM_MEM_PER_NODE"
else
    export THREADS=4
    export MEMORY=4096
fi
export REPO_DIR=/home/staff/haukurpj/SMT/
export WORK_DIR=/work/haukurpj/
export DATA_DIR=/work/haukurpj/data/
# Don't use language endings.
export LANGS="en is"
# Mono data
export MONO_DETOK="$DATA_DIR"mono/data-dedup-6578547-detok
export MONO_READY="$DATA_DIR"intermediary/lm-data

# Paralell
export TRAIN="$DATA_DIR"intermediary/train

# Truecasing
export TRUECASE_DATA="$DATA_DIR"intermediary/truecase-data
export TRUECASE_MODEL=preprocessing/preprocessing/resources/truecase-model

# LM
export LM_SURFACE_TRAIN="$DATA_DIR"train/form/lm-data
export LM_SURFACE_5="$DATA_DIR"train/form/blm
export LM_SURFACE_TEST="$DATA_DIR"test/form/

export TRAINING_DATA="$DATA_DIR"train/form/data
export DEV_DATA="$DATA_DIR"dev/form/data
export TEST_DIR="$DATA_DIR"test/raw/