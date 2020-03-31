#!/bin/bash
export WORK_DIR=/work/haukurpj/
export DATA_DIR=/work/haukurpj/data/
# Don't use language endings.
export TRUECASE_MODEL=preprocessing/preprocessing/resources/truecase-model
export LM_SURFACE_TRAIN="$DATA_DIR"train/form/lm-data
export LM_SURFACE_5="$DATA_DIR"train/form/blm
export LM_SURFACE_TEST="$DATA_DIR"test/form