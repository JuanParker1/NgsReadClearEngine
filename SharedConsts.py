import os
from pathlib import Path
from enum import Enum

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

PATH_TO_OUTPUT_PROCESSOR_SCRIPT = Path("/groups/pupko/alburquerque/NgsReadClearEngine/OutputProcessor.py")
CUSTOM_DB_NAME = 'custom' # the name of the custom db type

DF_LOADER_CHUCK_SIZE = 1e6
RESULTS_COLUMNS_TO_KEEP = ['is_classified', 'read_name', 'max_specie', 'classified_species', 'read_length', 'max_k_mer_p',
                           'all_classified_K_mers', 'split']
SUMMARY_RESULTS_COLUMN_NAMES = ['percentage_of_reads', 'number_of_reads_under', 'number_of_reads_exact', 'rank_code',
                                'ncbi_taxonomyID', 'name']
UNCLASSIFIED_COLUMN_NAME = 'Non Bacterial'
KRAKEN_UNCLASSIFIED_COLUMN_NAME = 'unclassified (taxid 0)'
UNCLASSIFIED_BACTERIA_NAME = 'Unclassified Contamination'
UNCLASSIFIED_BACTERIA_ID = '-1'

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
LONG_RUNNING_JOBS_NAME = 'LongRunning'
QUEUE_JOBS_NAME = 'Queue'
NEW_RUNNING_JOBS_NAME = 'NewRunning'
FINISHED_JOBS_NAME = 'Finished'
ERROR_JOBS_NAME = 'Error'
WEIRD_BEHAVIOR_JOB_TO_CHECK = ''
PATH2SAVE_PROCESS_DICT = r'SavedObjects/processes.dict'
INTERVAL_BETWEEN_LISTENER_SAMPLES = 5  # in seconds


# post processing
POSTPROCESS_JOB_PREFIX = 'PP'
POSTPROCESS_JOB_QUEUE_NAME = 'itaym'
NUBMER_OF_CPUS_POSTPROCESS_JOB = '1'
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

source /powerapps/share/miniconda3-4.7.12/etc/profile.d/conda.sh
conda activate NGScleaner

sleep {sleep_interval}

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

gzip -f "$output_path"

rm "$output_pathTemp"
rm "$Temp_new_unclassified_seqs"
'''

class EMAIL_CONSTS:
    FINISHED_TITLE = f'Genomefltr - Job finished'
    FINISHED_CONTENT = '''Thanks, for using GenomeFLTR\nYour results are at:\nhttp://genomefltr.tau.ac.il/process_state/{process_id}\nPlease, remember to cite us'''
    CRASHED_TITLE = f'Genomefltr - Job crashed'
    CRASHED_CONTENT = '''Thanks, for using GenomeFLTR\nYour results are at:\nhttp://genomefltr.tau.ac.il/process_state/{process_id}\nPlease, remember to cite us'''
    SUBMITTED_TITLE = f'Genomefltr - Job submitted'
    SUBMITTED_CONTENT = '''Thanks, for using GenomeFLTR\nYour job has been submitted, you can check the status at:\nhttp://genomefltr.tau.ac.il/process_state/{process_id}\nAn update will be sent uppon completion'''


class State(Enum):
    Running = 1
    Finished = 2
    Crashed = 3
    Waiting = 4
    Init = 5
    Queue = 6


class UI_CONSTS:
    SPECIES_FORM_PREFIX = 'species' # prefix for the form of the custom DB input (passed from home to __init__)
    KRAKEN_MAX_CUSTOM_SPECIES = 3 # max inputs in the home when pressing the custom DB
    
    static_folder_path = 'gifs/'
    states_gifs_dict = {
        State.Running: {
            "background": "#ffffff",
            "gif_id": "D5GyCFkInbJlu"
        },
        State.Finished: {
            "background": "#1674d2",
            "gif_id": "TvLuZ00OIADoQ"
        },
        State.Crashed: {
            "background": "#1674d2",
            "gif_id": "TvLuZ00OIADoQ"
        },
        State.Waiting:  {
            "background": "#1674d2",
            "gif_id": "TvLuZ00OIADoQ"
        },
        State.Init:  {
            "background": "#1674d2",
            "gif_id": "TvLuZ00OIADoQ"
        },
        State.Queue:  {
            "background": "#1674d2",
            "gif_id": "TvLuZ00OIADoQ"
        }
    }

    
    states_text_dict = {
        State.Running: "Your process is running",
        State.Finished: "Your process finished... Redirecting to results page", #TODO is needed??
        State.Crashed: "Your process crashed\n we suggest you rerun the process.", #TODO finish
        State.Waiting: "We currently run other processes :( \n Your process will start soon",
        State.Init: "We are verifing your input, your process will start shortly",
        State.Queue: "Job is queued",
    }
    
    global allowed_files_str  # todo: Edo, do we have to use a global var?
    ALLOWED_EXTENSIONS = {'fasta', 'fastq', 'gz', 'txt'}
    allowed_files_str = ', '.join(ALLOWED_EXTENSIONS) #better to path string than list


    class UI_Errors(Enum):
        UNKNOWN_PROCESS_ID = 'The provided process id does not exist'
        INVALID_EXPORT_PARAMS ='invalid paramters for export'
        POSTPROCESS_CRASH = 'can\'t postprocess'
        INVALID_MAIL = 'invalid mail'
        CANT_ADD_PROCESS = 'can\'t add search process'
        INVALID_FILE = f'invalid file or file extenstion, please use a valid: {allowed_files_str} file'
        EXPORT_FILE_UNAVAILABLE = f'failed to export file, try to rerun the file'
        PAGE_NOT_FOUND = 'The requested page does not exist'
        INVALID_SPECIES_LIST = 'Some of the species inserted to the custom DB are invalid'
        JOB_CRASHED = 'Your processed crashed... Make sure your input is valid'

    PROCESS_INFO_PP = "We are processing your request, This may take several minutes. You may close this window, An email will be sent upon completion"
    PROCESS_INFO_KR = "We are processing your request, This may take several minutes for small files and several hours for larger ones. Please close this window, An email will be sent upon completion"

    TEXT_TO_RELOAD_HTML = "update" # empty string not allowed! will cause massive bug!
    FETCH_UPDATE_INTERVAL_HTML_SEC = 15 # should be greater than 5 (keep-alive timeout mod_wsgi).