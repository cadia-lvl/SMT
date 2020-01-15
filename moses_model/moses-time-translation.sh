#!/bin/bash
#SBATCH --job-name=moses-time-translation.sh
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=16GB
#SBATCH --time=1:00:00

MODEL_NAME=en-is-mideind-v2
time singularity run -B /work/haukurpj/$MODEL_NAME/binarised:/work/haukurpj/$MODEL_NAME/binarised docker://haukurp/moses-smt:is-en-improved /opt/moses/bin/moses -f /work/haukurpj/$MODEL_NAME/binarised/moses.ini < /work/haukurpj/$MODEL_NAME/binarised/parice-test-final.en >/work/haukurpj/$MODEL_NAME/binarised/parice-test-final.translated
