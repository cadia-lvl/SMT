#!/bin/bash

#SBATCH --job-name=haukur-jupyter
#SBATCH --nodes=1
#SBATCH --cpus-per-task=20
#SBATCH --mem=16GB
#SBATCH --time=2-14:00:00
#SBATCH --output=server.out
#SBATCH --error=server.out

source ~/anaconda3/etc/profile.d/conda.sh
conda activate jupyter 

export MOSES_SUITE=/home/staff/$USER/moses/MosesSuite
export MOSESDECODER=/home/staff/$USER/moses/mosesdecoder
export MOSESDECODER_TOOLS=/home/staff/$USER/moses/tools
export WORKING_DIR=/mnt/scratch/smt
export MODEL_DIR=$PWD
export THREADS=20

port=8080

jupyter-notebook --no-browser --port $port --notebook-dir=$(pwd)
