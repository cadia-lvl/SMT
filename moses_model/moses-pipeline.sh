#!/bin/bash
#SBATCH --job-name=moses-pipeline
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1GB
#SBATCH --time=0:01:00
#SBATCH --output=/home/staff/haukurpj/%j-%x.out
set -euxo

dir_name=~/SMT/moses_model

jid_prep=$(sbatch --partition=longrunning $dir_name/moses-prep.sh | awk -F' ' '{print $4}')
jid_lm=$(sbatch --partition=longrunning --dependency=afterok:$jid_prep $dir_name/moses-lm.sh | awk -F' ' '{print $4}')
jid_train=$(sbatch --partition=longrunning --dependency=afterok:$jid_lm $dir_name/moses-train.sh | awk -F' ' '{print $4}')
jid_tune=$(sbatch --partition=longrunning --dependency=afterok:$jid_train $dir_name/moses-tune.sh | awk -F' ' '{print $4}')
jid_binarise=$(sbatch --partition=longrunning --dependency=afterok:$jid_tune $dir_name/moses-binarise.sh | awk -F' ' '{print $4}')
jid_evaluate=$(sbatch --partition=longrunning --dependency=afterok:$jid_binarise $dir_name/moses-evaluate.sh | awk -F' ' '{print $4}')

