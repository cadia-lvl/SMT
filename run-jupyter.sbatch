#!/bin/bash

#SBATCH --job-name=haukur-singularity-jupyter
#SBATCH --nodes=1
#SBATCH --cpus-per-task=40
#SBATCH --mem=32GB
#SBATCH --time=2-14:00:00
#SBATCH --output=server.out
#SBATCH --error=server.out


THREADS=40
TAG=1.1.1

SINGULARITYENV_THREADS=$THREADS singularity exec -B /scratch/smt:/work -B $PWD:/project docker://haukurp/moses-lvl:$TAG /bin/bash -c "/opt/conda/envs/jupyter/bin/jupyter notebook --notebook-dir=/project --ip='*' --port=8888 --no-browser --allow-root"
