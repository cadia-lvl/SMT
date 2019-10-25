#!/bin/bash

#SBATCH --job-name=haukur-singularity-jupyter
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64GB
#SBATCH --time=2-14:00:00
#SBATCH --output=server.out
#SBATCH --error=server.out

singularity exec -B $PWD:/opt/work docker://haukurp/moses-lvl:0.4 /bin/bash -c "/opt/conda/envs/jupyter/bin/jupyter notebook --notebook-dir=/opt/work --ip='*' --port=8888 --no-browser --allow-root"
