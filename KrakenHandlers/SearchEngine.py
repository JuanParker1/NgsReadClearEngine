import pathlib
import subprocess
from subprocess import PIPE
import os
from SharedConsts import BASE_PATH_TO_KRAKEN_SCRIPT, KRAKEN_SEARCH_SCRIPT_COMMAND, KRAKEN_DB_NAME, KRAKEN_JOB_TEMPLATE, \
    KRAKEN_JOB_QUEUE_NAME, NUBMER_OF_CPUS_KRAKEN_SEARCH_JOB, KRAKEN_JOB_PREFIX, PATH_TO_OUTPUT_PROCESSOR_SCRIPT, \
    CODE_BASE_PATH, RESULTS_SUMMARY_FILE_NAME, INPUT_CLASSIFIED_FILE_NAME, INPUT_UNCLASSIFIED_FILE_NAME, \
    TEMP_CLASSIFIED_IDS, TEMP_UNCLASSIFIED_IDS


class SearchEngine:
    """
    a class holding all code related to running the kraken2 search - assumes all inputs are valid
    """

    @staticmethod
    def kraken_search(input_path, run_parameters):
        """
        this function actually preforms the kraken2 search
        :param input_path: path to input query file
        :param run_parameters: a dictionary with the kraken run parameters
        :return: created job id, path to results
        """
        # create the job
        job_unique_id = str(pathlib.Path(input_path).parent.stem)
        temp_script_path = pathlib.Path().resolve() / f'temp_kraken_search_running_file_{job_unique_id}.sh'
        results_file_path = pathlib.Path(input_path).parent / 'results.txt'
        report_path = pathlib.Path(input_path).parent / RESULTS_SUMMARY_FILE_NAME
        classified_input_path = pathlib.Path(input_path).parent / INPUT_CLASSIFIED_FILE_NAME
        unclassified_input_path = pathlib.Path(input_path).parent / INPUT_UNCLASSIFIED_FILE_NAME
        temp_script_text = SearchEngine._create_kraken_search_job_text(input_path, run_parameters,
                                                                       job_unique_id, results_file_path,
                                                                       report_path, classified_input_path,
                                                                       unclassified_input_path)

        # run the job
        with open(temp_script_path, 'w+') as fp:
            fp.write(temp_script_text)
        terminal_cmd = f'/opt/pbs/bin/qsub {str(temp_script_path)}'
        job_run_output = subprocess.run(terminal_cmd, stdout=PIPE, stderr=PIPE, shell=True)
        os.remove(temp_script_path)

        return job_run_output.stdout.decode('utf-8').split('.')[0], results_file_path

    @staticmethod
    def _create_kraken_search_job_text(query_path, run_parameters, job_unique_id, result_path, report_path,
                                       classified_input_path, unclassified_input_path):
        """
        this function creates the text for the .sh file that will run the job - assumes everything is valid
        :param query_path: path to the query file
        :param run_parameters: additional run parameters
        :param job_unique_id: the jobs unique id (used to identify everything related to this run)
        :param result_path: where to put the kraken results
        :param report_path: where to put the kraken results report
        :param classified_input_path: where to put the split classified input
        :param unclassified_input_path: where to put the split unclassified input
        :return: the text for the .sh file
        """
        run_parameters_string = SearchEngine._create_parameter_string(run_parameters)
        job_name = f'{KRAKEN_JOB_PREFIX}_{job_unique_id}'
        kraken_run_command = BASE_PATH_TO_KRAKEN_SCRIPT / KRAKEN_SEARCH_SCRIPT_COMMAND
        db_path = BASE_PATH_TO_KRAKEN_SCRIPT / KRAKEN_DB_NAME
        job_logs_path = str(pathlib.Path(query_path).parent) + '/'
        return KRAKEN_JOB_TEMPLATE.format(queue_name=KRAKEN_JOB_QUEUE_NAME,
                                          cpu_number=NUBMER_OF_CPUS_KRAKEN_SEARCH_JOB, job_name=job_name,
                                          error_files_path=job_logs_path,
                                          output_files_path=job_logs_path,
                                          kraken_base_folder=CODE_BASE_PATH,
                                          kraken_command=kraken_run_command, db_path=db_path, query_path=query_path,
                                          kraken_results_path=result_path,
                                          path_to_output_processor=str(PATH_TO_OUTPUT_PROCESSOR_SCRIPT),
                                          additional_parameters=run_parameters_string,
                                          report_file_path=report_path,
                                          classified_ids_results=classified_input_path,
                                          unclassified_ids_results=unclassified_input_path,
                                          classified_ids_list=result_path.parent / TEMP_CLASSIFIED_IDS,
                                          unclassified_ids_list=result_path.parent / TEMP_UNCLASSIFIED_IDS)

    @staticmethod
    def _create_parameter_string(run_parameters):
        if not run_parameters:
            return ''
        parameter_string_arr = [str(param_name) + ' ' + str(param_value) + ' ' for
                                param_name, param_value in run_parameters.items()]
        return '--' + ' --'.join(parameter_string_arr)
