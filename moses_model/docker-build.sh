#!/bin/bash
set -euxo
MODEL_NAME=$1
DOCKER_IMAGE="haukurp/moses-smt:$MODEL_NAME"
THIS_DIR=$(dirname "$0")
# Afrita líkanið yfir á núverandi vél.
scp -r haukurpj@terra.hir.is:/work/haukurpj/"$MODEL_NAME"/binarised "$THIS_DIR"/trained_model
# Laga skráarendingar.
sed -i 's|work/.*/binarised|work|g' "$THIS_DIR"/trained_model/moses.ini
docker build -t "$DOCKER_IMAGE" "$THIS_DIR"
rm -rf "$THIS_DIR"/trained_model
docker push "$DOCKER_IMAGE"