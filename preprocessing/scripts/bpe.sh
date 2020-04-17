#!/bin/bash
#SBATCH --job-name=bpe
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=16GB
#SBATCH --time=1:00:00
#SBATCH --output=%x-%j.out
#SBATCH --chdir=/home/staff/haukurpj/SMT
# e=fail on pipeline, u=fail on unset var, x=trace commands
set -ex

source environment.sh
FIRST_STEP=1
LAST_STEP=3

EXTENSION="-bpe-train-30"
BPE_TRAIN="$TRAINING_DATA"
BPE_TRAINING_DATA="$TRAINING_DATA""$EXTENSION"
BPE_DEV_DATA="$DEV_DATA""$EXTENSION"
BPE_SURFACE_TRAIN="$LM_SURFACE_TRAIN""$EXTENSION"

function train_bpe() {
    LANG="$1"
    ARGUMENT="|--input=$BPE_TRAIN.$LANG|--model_prefix=preprocessing/preprocessing/resources/$LANG$EXTENSION|--model_type=bpe|--input_sentence_size=5000000|--vocab_size=$VOCAB_SIZE|--character_coverage=1.0"
    # We don't want to install the C++ version, so we need the Python version
    preprocessing/main.py train-bpe "$ARGUMENT"
}
VOCAB_SIZE=30000
if ((FIRST_STEP <= 1 && LAST_STEP >= 1)); then
    train_bpe is
    train_bpe en
fi

# Apply the bpe tokenization to train and dev
if ((FIRST_STEP <= 2 && LAST_STEP >= 2)); then
    for LANG in $LANGS; do
        preprocessing/main.py tokenize "$TRAINING_DATA"."$LANG" "$BPE_TRAINING_DATA"."$LANG" "$LANG" --tokenizer bpe --model preprocessing/preprocessing/resources/"$LANG""$EXTENSION".model --threads "$THREADS"
        preprocessing/main.py tokenize "$DEV_DATA"."$LANG" "$BPE_DEV_DATA"."$LANG" "$LANG" --tokenizer bpe --model preprocessing/preprocessing/resources/"$LANG""$EXTENSION".model --threads "$THREADS"
    done
fi

if ((FIRST_STEP <= 3 && LAST_STEP >= 3)); then
    for LANG in $LANGS; do
        preprocessing/main.py tokenize "$LM_SURFACE_TRAIN"."$LANG" "$BPE_SURFACE_TRAIN"."$LANG" "$LANG" --tokenizer bpe --model preprocessing/preprocessing/resources/"$LANG""$EXTENSION".model --threads "$THREADS"
    done
fi