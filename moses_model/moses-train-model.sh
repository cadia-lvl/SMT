#!/bin/bash
set -euxo

#SBATCH --job-name=train-moses
#SBATCH --nodes=1
#SBATCH --cpus-per-task=15
#SBATCH --mem=32GB
#SBATCH --time=18:00:00
#SBATCH --output=server.out
#SBATCH --error=server.out
export SINGULARITYENV_THREADS=$SLURM_CPUS_PER_TASK
export SINGULARITYENV_MEMORY=$SLURM_MEM_PER_NODE
MOSES_TAG="1.0.0"

WORK_DIR="/work/haukurpj"
TRAINING_DATA_DIR="${WORK_DIR}/process"

LANG_FROM="en"
LANG_TO="is"
MODIFIER="test"
MODEL_NAME="${LANG_FROM}-${LANG_TO}-${MODIFIER}"
MODEL_DIR="${WORK_DIR}/${MODEL_NAME}"
TRAINING_DATA="${TRAINING_DATA_DIR}/parice-train-final"

CLEAN_MIN_LENGTH=1
CLEAN_MAX_LENGTH=70
CLEAN_DATA="${TRAINING_DATA_DIR}/train-${MODEL_NAME}"
singularity exec \
	-B $WORK_DIR:$WORK_DIR \
	docker://haukurp/moses-smt:$TAG \
	opt/moses/scripts/training/clean-corpus-n.perl $TRAINING_DATA $LANG_FROM $LANG_TO $CLEAN_DATA $CLEAN_MIN_LENGTH $CLEAN_MAX_LENGTH
