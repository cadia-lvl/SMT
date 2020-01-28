#!/bin/bash
#SBATCH --job-name=moses-pipeline
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1GB
#SBATCH --time=8:00:00
set -euxo

dir_name=~/SMT/moses_model

jid_prep=$(sbatch $dir_name/moses-prep.sh)
jid_lm=$(sbatch --dependency=afterok:$jid_prep $dir_name/moses-lm.sh)
jid_train=$(sbatch --dependency=afterok:$jid_lm $dir_name/moses-train.sh)
jid_tune=$(sbatch --dependency=afterok:$jid_train $dir_name/moses-tune.sh)
jid_binarise=$(sbatch --dependency=afterok:$jid_tune $dir_name/moses-binarise.sh)
jid_evaluate=$(sbatch --dependency=afterok:$jid_binarise $dir_name/moses-evaluate.sh)

