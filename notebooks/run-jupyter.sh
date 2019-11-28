#!/bin/bash

PORT=8889
TAG=1.0.0
PY_ENV=/home/haukur/.pyenv/versions/3.7.5/envs/notebook/bin
WORK_DIR=/home/haukur/SMT/data
NOTEBOOK_DIR=/home/haukur/SMT/notebooks

export SINGULARITYENV_THREADS=4
export SINGULARITYENV_MEMORY=8564
singularity exec \
	-B $WORK_DIR:/work \
	-B $NOTEBOOK_DIR:/project \
	-B $PY_ENV:$PY_ENV \
	docker://haukurp/moses-smt:$TAG \
	/bin/bash -c "export PATH=$PATH:$PY_ENV && $PY_ENV/jupyter notebook --notebook-dir=/project --ip='*' --port=$PORT --no-browser --allow-root"
