#!/bin/bash
source /data/tools/anaconda/etc/profile.d/conda.sh
conda activate notebook

PICKLE_FILE='/work/haukurpj/data/filtered/Parice1.0/filtered.pickle'
OUTPUT_DIR='/work/haukurpj/data/mapped'
python "$PWD"/map.py write $PICKLE_FILE $OUTPUT_DIR --lemma --threads 20
