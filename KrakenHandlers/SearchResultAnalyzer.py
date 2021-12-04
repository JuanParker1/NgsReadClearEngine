import subprocess
from SharedConsts import POST_PROCESS_COMMAND_TEMPLATE
from subprocess import PIPE
import pathlib
import os


def run_post_process(path_to_classified_results, path_to_final_result_file, path_to_unclassified_results,
                     classification_threshold, species_to_filter_on, path_to_original_unclassified_data,
                     path_to_original_classified_data):
    """
    this function runs the post process filtering of classified to unclassified results
    :param path_to_classified_results: path to classified results file
    :param path_to_final_result_file: path to final data frame to export
    :param path_to_unclassified_results: path to Unclassified results file
    :param classification_threshold: threshold to determine "classified" results as "unclassified" results
    :param species_to_filter_on: list of species to KEEP classified
    :param path_to_original_unclassified_data: Path to fasta file of unclassified input seqs
    :param path_to_original_classified_data: Path to fasta file of classified input seqs
    :return:
    """
    species_to_filter_on_string = str(species_to_filter_on).strip('[]').replace('\'', "")
    command_to_run = POST_PROCESS_COMMAND_TEMPLATE.format(path_to_classified_results=path_to_classified_results,
                                                          path_to_final_result_file=path_to_final_result_file,
                                                          path_to_unclassified_results=path_to_unclassified_results,
                                                          classification_threshold=classification_threshold,
                                                          species_to_filter_on=species_to_filter_on_string,
                                                          path_to_original_unclassified_data=path_to_original_unclassified_data,
                                                          path_to_original_classified_data=path_to_original_classified_data)
    subprocess.call(command_to_run, stdout=PIPE, stderr=PIPE, shell=True)
