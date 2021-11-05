from pathlib import Path

# PBS Listener consts
JOB_NUMBER_COL = 'job_number'
JOB_NAME_COL = 'job_name'
JOB_STATUS_COL = 'job_status'
JOB_ELAPSED_TIME = 'elapsed_time'
JOB_CHANGE_COLS = [JOB_NUMBER_COL, JOB_NAME_COL, JOB_STATUS_COL]
QstatDataColumns = [JOB_NUMBER_COL, 'username', 'queue', JOB_NAME_COL, 'session_id', 'nodes', 'cpus', 'req_mem',
                    'req_time', JOB_STATUS_COL, JOB_ELAPSED_TIME]
SRVER_USERNAME = 'alburquerque'
JOB_RUNNING_TIME_LIMIT_IN_HOURS = 10

# Job listener and management function naming
LONG_RUNNING_JOBS_NAME = ''  # todo: edo put here what you want
QUEUE_JOBS_NAME = ''  # todo: edo put here what you want
NEW_RUNNING_JOBS_NAME = ''  # todo: edo put here what you want
FINISHED_JOBS_NAME = ''  # todo: edo put here what you want
FINISHED_JOBS_ERROR = ''  # todo: edo put here what you want
WEIRD_BEHAVIOR_JOB_TO_CHECK = '' # todo: edo put here what you want

# Kraken Variables
BASE_PATH_TO_KRAKEN_SCRIPT = Path("/groups/pupko/alburquerque/Kraken/")
KRAKEN_SEARCH_SCRIPT_COMMAND = "kraken2"
KRAKEN_DB_NAME = "Bacteria"  # assuming the DB is in the same BASE folder as the kraken script
KRAKEN_RESULTS_FILE_PATH = BASE_PATH_TO_KRAKEN_SCRIPT / "Temp_Job_{job_unique_id}_results.txt"

# Kraken Job variables
KRAKEN_JOB_QUEUE_NAME = 'itaym'
NUBMER_OF_CPUS_KRAKEN_SEARCH_JOB = '10'
KRAKEN_JOB_PREFIX = 'KR'

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
cd {kraken_base_folder}
PYTHONPATH=$(pwd)

{kraken_command} --db "{db_path}" "{query_path}" --output "{kraken_results_path} {additional_parameters}"

'''
