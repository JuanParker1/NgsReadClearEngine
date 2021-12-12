import os
import SharedConsts as sc
from KrakenHandlers.SearchEngine import SearchEngine
from KrakenHandlers.SearchResultAnalyzer import run_post_process
from Job_Manager_Thread_Safe import Job_Manager_Thread_Safe
from utils import logger


class Job_Manager_Thread_Safe_GenomeFltr:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str, func2update_html_kraken, func2update_html_postprocess):
        self.__input_file_name = input_file_name
        self.__func2update_html_kraken = func2update_html_kraken
        self.__func2update_html_postprocess = func2update_html_postprocess
        self.__search_engine = SearchEngine()
        function2call_processes_changes_state = {
            sc.KRAKEN_JOB_PREFIX: self.__func2update_html_kraken,
            sc.POSTPROCESS_JOB_PREFIX: self.__func2update_html_postprocess
        }
        function2append_process = {
            sc.KRAKEN_JOB_PREFIX: self.__kraken_process,
            sc.POSTPROCESS_JOB_PREFIX: self.__postprocess_process
        }
        self.__job_manager = Job_Manager_Thread_Safe(max_number_of_process, upload_root_path, input_file_name, function2call_processes_changes_state, function2append_process)

    def __kraken_process(self, process_folder_path: str, email_address):
        logger.info(f'process_folder_path = {process_folder_path}')
        file2fltr = os.path.join(process_folder_path, self.__input_file_name)
        pbs_id, _ = self.__search_engine.kraken_search(file2fltr, None)
        return pbs_id
    
    def __postprocess_process(self, process_folder_path: str, k_threshold, species_list):
        logger.info(f'process_folder_path = {process_folder_path}')
        pbs_id = run_post_process(parent_folder, k_threshold, species_list)
        return pbs_id

    def get_running_process(self):
        return self.__job_manager.get_running_process()

    def get_waiting_process(self):
        return self.__job_manager.get_waiting_process()

    def add_kraken_process(self, process_id: str, email_address):
        logger.info(f'process_id = {process_id}')
        self.__job_manager.add_process(process_id, sc.KRAKEN_JOB_PREFIX, email_address)

    def add_postprocess(self, process_id: str, email_address):
        logger.info(f'process_id = {process_id}')
        self.__job_manager.add_process(process_id, sc.POSTPROCESS_JOB_PREFIX, k_threshold, species_list)

    def get_job_state(self, process_id: str, job_prefix: str):
        logger.info(f'process_id = {process_id} job_prefix = {job_prefix}')
        return self.__job_manager.get_job_state(process_id, job_prefix)
