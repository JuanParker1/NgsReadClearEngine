from KrakenHandlers.KrakenConsts import KRAKEN_CUSTOM_DB_JOB_TEMPLATE, KRAKEN_CUSTOM_DB_SCRIPT_COMMAND,\
    BASE_PATH_TO_KRAKEN_SCRIPT, KRAKEN_CUSTOM_DB_JOB_PREFIX, NUBMER_OF_CPUS_KRAKEN_SEARCH_JOB, KRAKEN_JOB_QUEUE_NAME, \
    KRAKEN_CUSTOM_DB_NAME_PREFIX, MAX_CUSTOM_DB_RETRIES, KRAKEN_SEARCH_SCRIPT_COMMAND, CUSTOM_DB_TESTING_TMP_FILE
import pathlib
from utils import logger
from subprocess import PIPE, run
import pandas as pd


class KrakenCustomDbCreator:

    @staticmethod
    def create_custom_db(user_unique_id: str, path_to_fasta_file: pathlib.Path):
        """
        orchestrator method for creating a custom db from a fasta file.
        :param user_unique_id: a unique id for the db identifying the user is belongs to
        :param path_to_fasta_file: path to the fasta file
        assumes fasta file is STRICTLY in the format:
        >SEQ_NAME NCBI_ACCESSION_NUMBER
        ACTUAL_SEQ
        may contain many seqs in this format
        :return: the name of the correctly created DB or None if unsuccessful
        """
        custom_db_name = KRAKEN_CUSTOM_DB_NAME_PREFIX + user_unique_id
        if (path_to_fasta_file.parent / custom_db_name).is_dir():
            return None  # the custom db already exists
        testing_output_path = path_to_fasta_file.parent / CUSTOM_DB_TESTING_TMP_FILE

        custom_db_job_sh = KrakenCustomDbCreator._parse_db_job_text(custom_db_name, path_to_fasta_file,
                                                                    testing_output_path)
        temp_script_path = path_to_fasta_file.parent / f'temp_kraken_custom_db_job_file_{custom_db_job_sh}.sh'
        with open(temp_script_path, 'w+') as fp:
            fp.write(custom_db_job_sh)

        successful_test = False
        for i in range(MAX_CUSTOM_DB_RETRIES):
            # run the job
            logger.info(f'submitting job, temp_script_path = {temp_script_path}:')
            terminal_cmd = f'/opt/pbs/bin/qsub {str(temp_script_path)}'
            job_run_output = run(terminal_cmd, stdout=PIPE, stderr=PIPE, shell=True)
            # once the db is created run the testing
            testing_res = pd.read_csv(testing_output_path, sep='\t', header=None)
            testing_res.rename(columns={0: 'is_classified', 1: "read_name", 2: "classified_species", 3: "read_length",
                                        4: "all_classified_K_mers"}, inplace=True)
            if 'U' not in testing_res['is_classified'].unique():
                successful_test = True
                break

        if successful_test:
            return custom_db_name

        else:
            return None

    @staticmethod
    def _parse_db_job_text(custom_db_name: str, path_to_fasta_file: pathlib.Path, testing_output_path: pathlib.Path):
        """
        parses the .sh file to be submitted for the custom creation job
        :param custom_db_name: name of the custom db to be created
        :param path_to_fasta_file: path to the fasta file
        :param testing_output_path: path to testing results path
        :return:
        """
        queue_name = KRAKEN_JOB_QUEUE_NAME
        cpu_number = NUBMER_OF_CPUS_KRAKEN_SEARCH_JOB
        job_name = f'{KRAKEN_CUSTOM_DB_JOB_PREFIX}_{custom_db_name}'
        job_logs_path = str(pathlib.Path(path_to_fasta_file).parent) + '/'
        kraken_base_folder = str(BASE_PATH_TO_KRAKEN_SCRIPT)
        custom_db_name = custom_db_name
        custom_db_sh_text = KRAKEN_CUSTOM_DB_JOB_TEMPLATE.format(queue_name=queue_name, cpu_number=cpu_number,
                                                                 job_name=job_name, error_files_path=job_logs_path,
                                                                 output_files_path=job_logs_path,
                                                                 kraken_base_folder=kraken_base_folder,
                                                                 custom_db_name=custom_db_name,
                                                                 kraken_db_command=KRAKEN_CUSTOM_DB_SCRIPT_COMMAND,
                                                                 kraken_run_command=KRAKEN_SEARCH_SCRIPT_COMMAND,
                                                                 testing_output_path=str(testing_output_path),
                                                                 path_to_fasta_file=path_to_fasta_file)

        return custom_db_sh_text
