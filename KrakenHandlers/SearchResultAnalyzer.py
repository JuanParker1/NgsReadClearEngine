import os
import pathlib
import subprocess
from subprocess import PIPE

from SharedConsts import POST_PROCESS_COMMAND_TEMPLATE, RESULTS_FOR_OUTPUT_CLASSIFIED_RAW_FILE_NAME, \
    RESULTS_FOR_OUTPUT_UNCLASSIFIED_RAW_FILE_NAME, INPUT_UNCLASSIFIED_FILE_NAME, INPUT_CLASSIFIED_FILE_NAME, \
    FINAL_OUTPUT_FILE_NAME, POSTPROCESS_JOB_PREFIX, POSTPROCESS_JOB_QUEUE_NAME, NUBMER_OF_CPUS_POSTPROCESS_JOB
from utils import logger


def run_post_process(root_folder, classification_threshold, species_to_filter_on):
    """
    this function runs the post process filtering of classified to unclassified results
    :param root_folder: path to the client root folder
    :param classification_threshold: threshold to determine "classified" results as "unclassified" results
    :param species_to_filter_on: list of species to KEEP classified
    :return: the PBS job id
    """

    path_to_classified_results = os.path.join(root_folder, RESULTS_FOR_OUTPUT_CLASSIFIED_RAW_FILE_NAME)
    path_to_unclassified_results = os.path.join(root_folder, RESULTS_FOR_OUTPUT_UNCLASSIFIED_RAW_FILE_NAME)
    path_to_original_unclassified_data = os.path.join(root_folder, INPUT_UNCLASSIFIED_FILE_NAME)
    path_to_original_classified_data = os.path.join(root_folder, INPUT_CLASSIFIED_FILE_NAME)
    path_to_final_result_file = os.path.join(root_folder, FINAL_OUTPUT_FILE_NAME)
    #
    species_to_filter_on_string = str(species_to_filter_on).strip('[]').replace('\'', "")
    job_unique_id = str(pathlib.Path(root_folder).parent.stem)
    job_name = f'{POSTPROCESS_JOB_PREFIX}_{job_unique_id}'
    job_logs_path = str(root_folder) + '/'
    command_to_run = POST_PROCESS_COMMAND_TEMPLATE.format(path_to_classified_results=path_to_classified_results,
                                                          path_to_final_result_file=path_to_final_result_file,
                                                          path_to_unclassified_results=path_to_unclassified_results,
                                                          classification_threshold=classification_threshold,
                                                          species_to_filter_on=species_to_filter_on_string,
                                                          path_to_original_unclassified_data=path_to_original_unclassified_data,
                                                          path_to_original_classified_data=path_to_original_classified_data,
                                                          queue_name=POSTPROCESS_JOB_QUEUE_NAME,
                                                          cpu_number=NUBMER_OF_CPUS_POSTPROCESS_JOB,
                                                          job_name=job_name,
                                                          error_files_path=job_logs_path,
                                                          output_files_path=job_logs_path)

    # run post process on PBS
    temp_script_path = pathlib.Path().resolve() / f'TempPostProcessFor_{job_unique_id}.sh'

    with open(temp_script_path, 'w+') as fp:
        fp.write(command_to_run)
    logger.info(f'submitting job, temp_script_path = {temp_script_path}:')
    logger.debug(f'{command_to_run}')
    terminal_cmd = f'/opt/pbs/bin/qsub {str(temp_script_path)}'
    job_run_output = subprocess.run(terminal_cmd, stdout=PIPE, stderr=PIPE, shell=True)
    os.remove(temp_script_path)

    return job_run_output
