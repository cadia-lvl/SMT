#!/bin/bash
#SBATCH --job-name=moses-time-translation.sh
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=16GB
#SBATCH --time=1:00:00

MODEL_NAME=en-is-mideind-v2
FROM=en
time singularity run \
  -B /work/haukurpj/:/work/haukurpj/ \
   docker://haukurp/moses-smt:1.1.0 \
   /opt/moses/bin/moses -f /work/haukurpj/$MODEL_NAME/binarised/moses.ini \
    < /work/haukurpj/process/test/combined-processed.$FROM \
    > /work/haukurpj/$MODEL_NAME-combined-translated.$FROM
