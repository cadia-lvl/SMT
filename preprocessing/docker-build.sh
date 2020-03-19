#!/bin/bash
set -euxo
TAG=$1

TRUECASE_MODEL_IS=/work/haukurpj/data/train/truecase-model.form.is
TRUECASE_MODEL_EN=/work/haukurpj/data/train/truecase-model.form.en

THIS_DIR=$(dirname $(realpath "$0"))

scp haukurpj@torpaq.hir.is:"$TRUECASE_MODEL_IS" "$THIS_DIR"
scp haukurpj@torpaq.hir.is:"$TRUECASE_MODEL_EN" "$THIS_DIR"
docker build --no-cache -t haukurp/moses-lvl:$TAG $(dirname "$0")
# Clean-up on isle four
rm "$THIS_DIR"/truecase-model.form.is
rm "$THIS_DIR"/truecase-model.form.en
docker push haukurp/moses-lvl:$TAG