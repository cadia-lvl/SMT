#!/bin/bash
#SBATCH --job-name=moses-prep
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=10GB
#SBATCH --time=2:00:00
#SBATCH --output=/home/staff/haukurpj/%j-%x.out
set -euxo

dir_name=~/SMT/moses_model
source "$dir_name"/moses-definitions.sh

# This script prepares all directories and writes the description of the model hyperparameters to a file.
mkdir -p $MODEL_DIR
mkdir -p $MODEL_DATA
mkdir -p $MODEL_RESULTS

echo "name=$EXPERIMENT_NAME
from=$LANG_FROM
to=$LANG_TO
lm_extra=$LM_EXTRA_DATA
train=$TRAINING_DATA
dev=$DEV_DATA
test=$TEST_INPUT
ground-truth=$GROUND_TRUTH
clean_min=$CLEAN_MIN_LENGTH
clean_max=$CLEAN_MAX_LENGTH
lm_order=$LM_ORDER
alignment=$ALIGNMENT" > $MODEL_DIR/description.txt

# Data prep
run_in_singularity ${MOSESDECODER}/scripts/training/clean-corpus-n.perl $TRAINING_DATA $LANG_FROM $LANG_TO $CLEAN_DATA $CLEAN_MIN_LENGTH $CLEAN_MAX_LENGTH

