#!/bin/bash

#SBATCH --job-name=haukur-singularity-jupyter
#SBATCH --nodes=1
#SBATCH --cpus-per-task=14
#SBATCH --mem=32GB
#SBATCH --time=2-14:00:00
#SBATCH --output=server.out
#SBATCH --error=server.out

SINGULARITYENV_THREADS=14 singularity exec -B /scratch/smt:/work -B $PWD:/project docker://haukurp/moses-lvl:0.4 /bin/bash -c "/opt/conda/envs/jupyter/bin/jupyter notebook --notebook-dir=/project --ip='*' --port=8888 --no-browser --allow-root"
