import subprocess
from SharedConsts import POST_PROCESS_COMMAND_TEMPLATE, RESULTS_FOR_OUTPUT_CLASSIFIED_RAW_FILE_NAME, \
    RESULTS_FOR_OUTPUT_UNCLASSIFIED_RAW_FILE_NAME, INPUT_UNCLASSIFIED_FILE_NAME, INPUT_CLASSIFIED_FILE_NAME, \
    FINAL_OUTPUT_FILE_NAME
from subprocess import PIPE
import os


def run_post_process(root_folder, classification_threshold, species_to_filter_on):
    """
    this function runs the post process filtering of classified to unclassified results
    :param root_folder: path to the client root folder
    :param classification_threshold: threshold to determine "classified" results as "unclassified" results
    :param species_to_filter_on: list of species to KEEP classified
    :return:
    """
    # todo: params - root folder, threshold, species list . return: Path to result file

    path_to_classified_results = os.path.join(root_folder, RESULTS_FOR_OUTPUT_CLASSIFIED_RAW_FILE_NAME)
    path_to_unclassified_results = os.path.join(root_folder, RESULTS_FOR_OUTPUT_UNCLASSIFIED_RAW_FILE_NAME)
    path_to_original_unclassified_data = os.path.join(root_folder, INPUT_UNCLASSIFIED_FILE_NAME)
    path_to_original_classified_data = os.path.join(root_folder, INPUT_CLASSIFIED_FILE_NAME)
    path_to_final_result_file = os.path.join(root_folder, FINAL_OUTPUT_FILE_NAME)

    species_to_filter_on_string = str(species_to_filter_on).strip('[]').replace('\'', "")
    command_to_run = POST_PROCESS_COMMAND_TEMPLATE.format(path_to_classified_results=path_to_classified_results,
                                                          path_to_final_result_file=path_to_final_result_file,
                                                          path_to_unclassified_results=path_to_unclassified_results,
                                                          classification_threshold=classification_threshold,
                                                          species_to_filter_on=species_to_filter_on_string,
                                                          path_to_original_unclassified_data=path_to_original_unclassified_data,
                                                          path_to_original_classified_data=path_to_original_classified_data)
    subprocess.call(command_to_run, stdout=PIPE, stderr=PIPE, shell=True)

