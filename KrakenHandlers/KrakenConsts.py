from pathlib import Path

# todo replace all paths
CODE_BASE_PATH = Path("/groups/pupko/alburquerque/NgsReadClearEngine/")
BASE_PATH_TO_KRAKEN_SCRIPT = Path("/groups/pupko/alburquerque/Kraken/")
KRAKEN_SEARCH_SCRIPT_COMMAND = str(BASE_PATH_TO_KRAKEN_SCRIPT) + "/kraken2"
KRAKEN_CUSTOM_DB_SCRIPT_COMMAND = str(BASE_PATH_TO_KRAKEN_SCRIPT) + "/kraken2-build"

# assuming the DB is in the same BASE folder as the kraken script
KRAKEN_DB_NAMES = ["Bacteria", 'human', 'fungi', 'protozoa', 'UniVec', 'plasmid', 'archaea', 'Viral',
                   'Kraken Standard']
KRAKEN_RESULTS_FILE_PATH = BASE_PATH_TO_KRAKEN_SCRIPT / "Temp_Job_{job_unique_id}_results.txt"

# Kraken Search Job variables
KRAKEN_JOB_QUEUE_NAME = 'itaym'
NUBMER_OF_CPUS_KRAKEN_SEARCH_JOB = '10'
KRAKEN_JOB_PREFIX = 'KR'
KRAKEN_CUSTOM_DB_JOB_PREFIX = 'CDB'
KRAKEN_CUSTOM_DB_NAME_PREFIX = 'CustomDB_'
CUSTOM_DB_TESTING_TMP_FILE = 'CustomDbTestingRes.txt'
KRAKEN_JOB_TEMPLATE = '''
#!/bin/bash

#PBS -S /bin/bash
#PBS -r y
#PBS -q {queue_name}
#PBS -l ncpus={cpu_number}
#PBS -v PBS_O_SHELL=bash,PBS_ENVIRONMENT=PBS_BATCH
#PBS -N {job_name}
#PBS -e {error_files_path}
#PBS -o {output_files_path}

source /powerapps/share/miniconda3-4.7.12/etc/profile.d/conda.sh
conda activate NGScleaner
cd {kraken_base_folder}
PYTHONPATH=$(pwd)

sleep {sleep_interval}

{kraken_command} --db "{db_path}" "{query_path}" --output "{kraken_results_path}" --threads 20 --use-names --report {report_file_path} {additional_parameters}
python {path_to_output_processor} --outputFilePath "{kraken_results_path}"
cat {query_path} | seqkit grep -f {classified_ids_list}  -o {classified_ids_results}
cat {query_path} | seqkit grep -f {unclassified_ids_list}  -o {unclassified_ids_results}
rm {query_path}
'''

# Kraken Custom Db Creation
KRAKEN_CUSTOM_DB_JOB_TEMPLATE = '''
#!/bin/bash

#PBS -S /bin/bash
#PBS -r y
#PBS -q {queue_name}
#PBS -l ncpus={cpu_number}
#PBS -v PBS_O_SHELL=bash,PBS_ENVIRONMENT=PBS_BATCH
#PBS -N {job_name}
#PBS -e {error_files_path}
#PBS -o {output_files_path}

#source /powerapps/share/miniconda3-4.7.12/etc/profile.d/conda.sh
#conda activate NGScleaner
source /groups/pupko/alburquerque/miniconda3/etc/profile.d/conda.sh
conda activate RLworkshop

PYTHONPATH=$(pwd)

DB_NAME="{kraken_base_folder}{custom_db_name}"

for i in 1
do

    rm -r -f $DB_NAME
    
    mkdir $DB_NAME
    
    #/groups/pupko/alburquerque/Kraken/kraken2-build --db $DB_NAME --download-taxonomy --fast-build --threads 20
    
    mkdir $DB_NAME/taxonomy
    
    cp -R "{kraken_base_folder}Tax_Base/taxonomy/." $DB_NAME/taxonomy
    
    {kraken_db_command} --db $DB_NAME -add-to-library "{path_to_fasta_file}"
    
    {kraken_db_command} --db $DB_NAME --build --fast-build --threads 20
    
    {kraken_db_command} --db $DB_NAME --clean --fast-build --threads 20
    
    {kraken_run_command} --db /groups/pupko/alburquerque/Kraken/{custom_db_name} "{path_to_fasta_file}" --output "{testing_output_path}" --threads 20
    
    goodTest=python {path_to_validator_script} --TestingFastaPath "{testing_output_path}" 

    if [ "$goodTest" -eq 0 ]; then
        echo "Broken";
        break;
    fi
    
done

'''

