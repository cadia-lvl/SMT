#!/bin/bash
#SBATCH --job-name=moses-prep
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=10GB
#SBATCH --time=2:00:00
#SBATCH --output=/home/staff/haukurpj/%j-%x.out
set -euxo

source $1
# This script prepares all directories and writes the description of the model hyperparameters to a file.
mkdir -p $MODEL_DIR
mkdir -p $MODEL_DATA
mkdir -p $MODEL_RESULTS

cat $1 >$MODEL_DIR/definitions.sh

# Data prep
run_in_singularity ${MOSESDECODER}/scripts/training/clean-corpus-n.perl $TRAINING_DATA $LANG_FROM $LANG_TO $CLEAN_DATA $CLEAN_MIN_LENGTH $CLEAN_MAX_LENGTH
