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
FINAL_OUTPUT_FILE_NAME = Path('FilteredResults.txt.gz')
KRAKEN_SUMMARY_RESULTS_FOR_UI_FILE_NAME = Path('summary_stat_UI.json')
RANK_KRAKEN_TRANSLATIONS = {'U': 'Unclassified', 'R': 'Root', 'D': 'Domain', 'K': 'Kingdom', 'P': 'Phylum',
                            'C': 'Class', 'O': 'Order', 'F': 'Family', 'G': 'Genus', 'S': 'Species'}

PATH_TO_OUTPUT_PROCESSOR_SCRIPT = Path(
    "/groups/pupko/alburquerque/NgsReadClearEngine/OutputProcessor.py")  # todo: replace this with real path
DF_LOADER_CHUCK_SIZE = 1e6
RESULTS_COLUMNS_TO_KEEP = ['is_classified', 'read_name', 'max_specie', 'classified_species', 'read_length', 'max_k_mer_p',
                           'all_classified_K_mers', 'split']
SUMMARY_RESULTS_COLUMN_NAMES = ['percentage_of_reads', 'number_of_reads_under', 'number_of_reads_exact', 'rank_code',
                                'ncbi_taxonomyID', 'name']
UNCLASSIFIED_COLUMN_NAME = 'Non Bacterial'
KRAKEN_UNCLASSIFIED_COLUMN_NAME = 'unclassified (taxid 0)'

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
PATH2SAVE_PROCESS_DICT = r'SavedObjects/processes.dict'

# Kraken Variables
# todo replace all paths
CODE_BASE_PATH = Path("/groups/pupko/alburquerque/NgsReadClearEngine/")
BASE_PATH_TO_KRAKEN_SCRIPT = Path("/groups/pupko/alburquerque/Kraken/")
KRAKEN_SEARCH_SCRIPT_COMMAND = str(BASE_PATH_TO_KRAKEN_SCRIPT) + "/kraken2"
KRAKEN_DB_NAME = "Bacteria"  # assuming the DB is in the same BASE folder as the kraken script
KRAKEN_RESULTS_FILE_PATH = BASE_PATH_TO_KRAKEN_SCRIPT / "Temp_Job_{job_unique_id}_results.txt"

# Kraken Job variables
KRAKEN_JOB_QUEUE_NAME = 'itaym'
POSTPROCESS_JOB_QUEUE_NAME = KRAKEN_JOB_QUEUE_NAME
NUBMER_OF_CPUS_KRAKEN_SEARCH_JOB = '30'
NUBMER_OF_CPUS_POSTPROCESS_JOB = '1'
KRAKEN_JOB_PREFIX = 'KR'
POSTPROCESS_JOB_PREFIX = 'PP'
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

original_unclassified_data="{path_to_original_unclassified_data}"
original_classified_data="{path_to_original_classified_data}"
input_path="{path_to_classified_results}"
output_path="{path_to_final_result_file}"
output_pathTemp="{path_to_temp_file}"
Temp_new_unclassified_seqs="{path_to_temp_unclassified_file}"
string='{species_to_filter_on}'

# filter kraken results by query name and threshold
cat "$input_path" | awk -F "," '{{split(var,parts,","); for (i in parts) dict[parts[i]]; if ($6 <= {classification_threshold} || !($3 in dict)) print }}' var="${{string}}" | awk -F "," 'NR!=1 {{print $2}}' > "$output_pathTemp"

# filter original classified results
cat "$original_classified_data" | seqkit grep -f "$output_pathTemp"  -o "$Temp_new_unclassified_seqs"

# combine original unfiltered input with newly unclassified results
cat "$Temp_new_unclassified_seqs" "$original_unclassified_data" > "$output_path"

gzip "$output_path"

rm "$output_path"
rm "$output_pathTemp"
rm "$Temp_new_unclassified_seqs"
'''

class UI_CONSTS:
    static_folder_path = 'gifs/'
    states_gifs_dict = {
        State.Running: os.path.join(static_folder_path, "loading4.gif"),
        State.Finished: os.path.join(static_folder_path, "loading2.gif"), #TODO is needed??
        State.Crashed: "crashed", #TODO finish
        State.Waiting: os.path.join(static_folder_path, "loading1.gif"),
        State.Init: os.path.join(static_folder_path, "loading3.gif"),
        State.Queue: os.path.join(static_folder_path, "loading2.gif"),
    }
    
    states_text_dict = {
        State.Running: "Your process is running",
        State.Finished: "Your process finished... Redirecting to results page", #TODO is needed??
        State.Crashed: "Your process crashed\n we suggest you rerun the process.", #TODO finish
        State.Waiting: "We currently run other processes :( \n Your process will start soon",
        State.Init: "We are verifing your input, your process will start shortly",
        State.Queue: "Job is queued",
    }
    
    ALLOWED_EXTENSIONS = {'fasta', 'fastqc', 'gz'}
    allowed_files_str = ', '.join(ALLOWED_EXTENSIONS) #better to path string than list

    ALERT_USER_TEXT_UNKNOWN_PROCESS_ID = 'unknown process'
    ALERT_USER_TEXT_INVALID_EXPORT_PARAMS = 'invalid paramters for export'
    ALERT_USER_TEXT_POSTPROCESS_CRASH = 'can\'t postprocess'
    ALERT_USER_TEXT_NO_FILE_UPLOADED = 'insert file'
    ALERT_USER_TEXT_INVALID_MAIL = 'invalid mail'
    ALERT_USER_TEXT_CANT_ADD_PROCESS = 'can\'t add search process'
    ALERT_USER_TEXT_FILE_EXTENSION_NOT_ALLOWED = f'invalid file extenstion, please use one of the following: {allowed_files_str}'
    ALERT_USER_TEXT_EXPORT_FILE_UNAVAILABLE = f'failed to export file, try to rerun the file'

