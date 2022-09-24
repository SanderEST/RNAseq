#!/bin/bash
#SBATCH -n 1
#SBATCH -c 2
#SBATCH -J launch_cromwell
#SBATCH --mem=4000
#SBATCH -t 96:00:00


module load perl/5.30.1 python/3.8.6

#module load python/3.6.3/virtenv
#module load star-2.7
#module load perl-5.22.0

java -Dconfig.file=/gpfs/space/home/a71644/tools/cromwell_wdl/slurm.conf -jar \
/gpfs/space/home/a71644/tools/jars/cromwell-36.jar run \
/gpfs/space/home/a71644/tools/RNAseq/RNAseq.wdl \
-i RNAseq.inputs.json \
-o cromwell.options
