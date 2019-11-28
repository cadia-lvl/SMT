#!/bin/bash

#SBATCH --job-name=haukur-singularity-jupyter
#SBATCH --nodes=1
#SBATCH --cpus-per-task=15
#SBATCH --mem=32GB
#SBATCH --time=6-14:00:00
#SBATCH --output=server.out
#SBATCH --error=server.out

PORT=8889
TAG=1.0.0
PY_ENV=/home/staff/haukurpj/.pyenv/versions/3.7.5/envs/notebook/bin
WORK_DIR=/work/haukurpj
NOTEBOOK_DIR=/home/staff/haukurpj/SMT/notebooks

export SINGULARITYENV_THREADS=$SLURM_CPUS_PER_TASK
export SINGULARITYENV_MEMORY=$SLURM_MEM_PER_NODE
singularity exec \
	-B $WORK_DIR:/work \
	-B $NOTEBOOK_DIR:/project \
	-B $PY_ENV:$PY_ENV \
	docker://haukurp/moses-smt:$TAG \
	/bin/bash -c "export PATH=$PATH:$PY_ENV && $PY_ENV/jupyter notebook --notebook-dir=/project --ip='*' --port=$PORT --no-browser --allow-root"
