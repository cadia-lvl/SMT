#!/bin/bash

#SBATCH --job-name=haukur-singularity-jupyter
#SBATCH --nodes=1
#SBATCH --cpus-per-task=15
#SBATCH --mem=32GB
#SBATCH --time=6-14:00:00
#SBATCH --output=server.out
#SBATCH --error=server.out

PORT=8889
THREADS=15
TAG=1.2.0

SINGULARITYENV_THREADS=$THREADS singularity exec -B /work/haukurpj:/work -B $PWD:/project docker://haukurp/moses-lvl:$TAG /bin/bash -c "/opt/conda/envs/jupyter/bin/jupyter notebook --notebook-dir=/project --ip='*' --port=$PORT --no-browser --allow-root"
