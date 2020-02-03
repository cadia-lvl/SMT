#!/bin/bash
#SBATCH --job-name=moses-pipeline
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1GB
#SBATCH --time=0:01:00
#SBATCH --output=/home/staff/haukurpj/%j-%x.out
set -euxo

dir_name=~/SMT/moses_model
if [ $# -eq 1 ]; then
  DEFINITIONS_LOCATION=$1
else
  DEFINITIONS_LOCATION=$dir_name/definitions.sh
  echo "Using default location for definitions"
fi

jid_prep=$(sbatch --partition=longrunning $dir_name/moses-prep.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
jid_lm=$(sbatch --partition=longrunning --dependency=afterok:$jid_prep $dir_name/moses-lm.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
jid_train=$(sbatch --partition=longrunning --dependency=afterok:$jid_lm $dir_name/moses-train.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
jid_tune=$(sbatch --partition=longrunning --dependency=afterok:$jid_train $dir_name/moses-tune.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
jid_binarise=$(sbatch --partition=longrunning --dependency=afterok:$jid_tune $dir_name/moses-binarise.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
jid_evaluate=$(sbatch --partition=longrunning --dependency=afterok:$jid_binarise $dir_name/moses-evaluate.sh $DEFINITIONS_LOCATION | awk -F' ' '{print $4}')
