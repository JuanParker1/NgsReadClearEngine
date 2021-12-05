import os
from pathlib import Path
from utils import State

# OUTPUT consts
K_MER_COUNTER_MATRIX_FILE_NAME = Path('CounterMatrixForUI.csv')
RESULTS_FOR_OUTPUT_CLASSIFIED_RAW_FILE_NAME = Path('ResultsForPostProcessClassifiedRaw.csv')
RESULTS_SUMMARY_FILE_NAME = Path('summary_results.txt')
RESULTS_FOR_OUTPUT_UNCLASSIFIED_RAW_FILE_NAME = Path('ResultsForPostProcessUnClassifiedRaw.csv')
TEMP_CLASSIFIED_IDS = Path('TempClassifiedIds.txt')
TEMP_UNCLASSIFIED_IDS = Path('TempUnClassifiedIds.txt')
INPUT_CLASSIFIED_FILE_NAME = Path('classified.fasta')
INPUT_UNCLASSIFIED_FILE_NAME = Path('unclassified.fasta')
FINAL_OUTPUT_FILE_NAME = Path('FilteredResults.fasta')
PATH_TO_OUTPUT_PROCESSOR_SCRIPT = Path(
    "/groups/pupko/alburquerque/NgsReadClearEngine/OutputProcessor.py")  # todo: replace this with real path
DF_LOADER_CHUCK_SIZE = 1e6
RESULTS_COLUMNS_TO_KEEP = ['is_classified', 'read_name', 'classified_species', 'read_length', 'max_k_mer_p',
                           'all_classified_K_mers', 'split']
SUMMARY_RESULTS_COLUMN_NAMES = ['percentage_of_reads', 'number_of_reads_under', 'number_of_reads_exact', 'rank_code',
                                'ncbi_taxonomyID', 'name']
UNCLASSIFIED_COLUMN_NAME = 'unclassified (taxid 0)'

# PBS Listener consts
JOB_NUMBER_COL = 'job_number'
JOB_NAME_COL = 'job_name'
JOB_STATUS_COL = 'job_status'
JOB_ELAPSED_TIME = 'elapsed_time'
JOB_CHANGE_COLS = [JOB_NUMBER_COL, JOB_NAME_COL, JOB_STATUS_COL]
QstatDataColumns = [JOB_NUMBER_COL, 'username', 'queue', JOB_NAME_COL, 'session_id', 'nodes', 'cpus', 'req_mem',
                    'req_time', JOB_STATUS_COL, JOB_ELAPSED_TIME]
SRVER_USERNAME = 'bioseq'
JOB_RUNNING_TIME_LIMIT_IN_HOURS = 10

# Job listener and management function naming
LONG_RUNNING_JOBS_NAME = 'LongRunning'  # todo: edo put here what you want
QUEUE_JOBS_NAME = 'Queue'  # todo: edo put here what you want
NEW_RUNNING_JOBS_NAME = 'NewRunning'  # todo: edo put here what you want
FINISHED_JOBS_NAME = 'Finished'  # todo: edo put here what you want
ERROR_JOBS_NAME = 'Error'  # todo: edo put here what you want
WEIRD_BEHAVIOR_JOB_TO_CHECK = ''  # todo: edo put here what you want

# Kraken Variables
# todo replace all paths
CODE_BASE_PATH = Path("/groups/pupko/alburquerque/NgsReadClearEngine/")
BASE_PATH_TO_KRAKEN_SCRIPT = Path("/groups/pupko/alburquerque/Kraken/")
KRAKEN_SEARCH_SCRIPT_COMMAND = str(BASE_PATH_TO_KRAKEN_SCRIPT) + "/kraken2"
KRAKEN_DB_NAME = "Bacteria"  # assuming the DB is in the same BASE folder as the kraken script
KRAKEN_RESULTS_FILE_PATH = BASE_PATH_TO_KRAKEN_SCRIPT / "Temp_Job_{job_unique_id}_results.txt"

# Kraken Job variables
KRAKEN_JOB_QUEUE_NAME = 'itaym'
NUBMER_OF_CPUS_KRAKEN_SEARCH_JOB = '10'
KRAKEN_JOB_PREFIX = 'KR'
# todo: replace the conda env
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

source /groups/pupko/alburquerque/miniconda3/etc/profile.d/conda.sh
conda activate
cd {kraken_base_folder}
PYTHONPATH=$(pwd)

{kraken_command} --db "{db_path}" "{query_path}" --output "{kraken_results_path}" --threads 20 --use-names --report {report_file_path} {additional_parameters}
python {path_to_output_processor} --outputFilePath "{kraken_results_path}"
cat {query_path} | seqkit grep -f {classified_ids_list}  -o {classified_ids_results}
cat {query_path} | seqkit grep -f {unclassified_ids_list}  -o {unclassified_ids_results}
rm {query_path}
'''

# post processing

POST_PROCESS_COMMAND_TEMPLATE = '''
#!/bin/bash          

original_unclassified_data="{path_to_original_unclassified_data}"
original_classified_data="{path_to_original_classified_data}"
input_path="{path_to_classified_results}"
output_path="{path_to_final_result_file}"
output_pathTemp="Temp.txt"
Temp_new_unclassified_seqs="Temp_new_unclassified_seqs.fasta"
unclassified_path="{path_to_unclassified_results}"
string='{species_to_filter_on}'

# filter kraken results by query name and threshold
cat "$input_path" | awk -F "\\"*,\\"*" '{{split(var,parts,","); for (i in parts) dict[parts[i]]; if ($5 <= {classification_threshold} || !($3 in dict)) print }}' var="${{string}}" | awk -F "\\"*,\\"*" 'NR!=1 {{print $2}}' > "$output_pathTemp"

# filter original classified results
cat "$original_classified_data" | seqkit grep -f "$output_pathTemp"  -o "$Temp_new_unclassified_seqs"

# combine original unfiltered input with newly unclassified results
cat "$Temp_new_unclassified_seqs" "$original_unclassified_data" > "$output_path"

rm "$output_pathTemp"
rm "$Temp_new_unclassified_seqs"
'''

class UI_CONSTS:
    static_folder_path = 'gifs/'
    states_gifs_dict = {
        State.Running: os.path.join(static_folder_path, "loading4.gif"),
        State.Finished: os.path.join(static_folder_path, "loading2.gif"),
        State.Crashed: "crashed", #TODO finish
        State.Waiting: os.path.join(static_folder_path, "loading1.gif"),
        State.Init: os.path.join(static_folder_path, "loading3.gif"),
    }

