#!/bin/bash
#SBATCH --job-name=moses
#SBATCH --nodes=1
#SBATCH --cpus-per-task=10
#SBATCH --mem=16G
#SBATCH --chdir=/home/staff/haukurpj/SMT
#SBATCH --time=8:01:00
#SBATCH --output=%x-%j.out

WORK_DIR="/work/haukurpj"
export MOSESDECODER="/opt/moses"
export MOSESDECODER_TOOLS="/opt/moses_tools"
singularity exec \
  -B "$WORK_DIR":"$WORK_DIR" \
  -B /home/staff/haukurpj/SMT:/home/staff/haukurpj/SMT \
  -B /data/tools/anaconda:/data/tools/anaconda \
	docker://haukurp/moses-smt:1.1.0 \
  "$@"