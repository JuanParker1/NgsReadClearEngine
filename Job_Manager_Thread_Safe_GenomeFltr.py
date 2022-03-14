import os
import SharedConsts as sc
import KrakenHandlers.KrakenConsts as kc
from KrakenHandlers.SearchEngine import SearchEngine
from KrakenHandlers.SearchResultAnalyzer import run_post_process
from KrakenHandlers.DbUtils.CustomDbCreator import KrakenCustomDbCreator
from Job_Manager_Thread_Safe import Job_Manager_Thread_Safe
from utils import logger


class Job_Manager_Thread_Safe_GenomeFltr:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str, func2update_db_donwload, func2update_html_kraken, func2update_html_postprocess):
        self.__input_file_name = input_file_name
        self.__func2update_db_donwload = func2update_db_donwload
        self.__func2update_html_kraken = func2update_html_kraken
        self.__func2update_html_postprocess = func2update_html_postprocess
        self.__search_engine = SearchEngine()
        self.__db_creator = KrakenCustomDbCreator()
        function2call_processes_changes_state = {
            kc.KRAKEN_CUSTOM_DB_JOB_PREFIX: self.__func2update_db_donwload,
            kc.KRAKEN_JOB_PREFIX: self.__func2update_html_kraken,
            sc.POSTPROCESS_JOB_PREFIX: self.__func2update_html_postprocess
        }
        function2append_process = {
            kc.KRAKEN_CUSTOM_DB_JOB_PREFIX: self.__download_process,
            kc.KRAKEN_JOB_PREFIX: self.__kraken_process,
            sc.POSTPROCESS_JOB_PREFIX: self.__postprocess_process
        }
        paths2verify_process_ends = {
            #when the job crashes/ finished this file path will be checked to set the change to finished if file exists of crashed if file doesn't.
            #for a string of: '' it won't set the state
            kc.KRAKEN_CUSTOM_DB_JOB_PREFIX: lambda process_id: os.path.join(os.path.join(upload_root_path, process_id), kc.OUTPUT_MERGED_FASTA_FILE_NAME),
            kc.KRAKEN_JOB_PREFIX: lambda process_id: os.path.join(os.path.join(upload_root_path, process_id), sc.K_MER_COUNTER_MATRIX_FILE_NAME),
            sc.POSTPROCESS_JOB_PREFIX: lambda process_id: os.path.join(os.path.join(upload_root_path, process_id), sc.FINAL_OUTPUT_FILE_NAME)
        }
        self.__job_manager = Job_Manager_Thread_Safe(max_number_of_process, upload_root_path, input_file_name, function2call_processes_changes_state, function2append_process, paths2verify_process_ends)
    
    def __download_process(self, process_folder_path: str, email_address, species2download):
        logger.info(f'process_folder_path = {process_folder_path}')
        fasta_file_path = os.path.join(process_folder_path, kc.OUTPUT_MERGED_FASTA_FILE_NAME)
        pbs_id = self.__db_creator.create_custom_db(fasta_file_path, species2download)
        return pbs_id
    
    def __kraken_process(self, process_folder_path: str, email_address, db_type):
        logger.info(f'process_folder_path = {process_folder_path}')
        file2fltr = os.path.join(process_folder_path, self.__input_file_name)
        pbs_id, _ = self.__search_engine.kraken_search(file2fltr, None)
        return pbs_id
    
    def __postprocess_process(self, process_folder_path: str, k_threshold, species_list):
        logger.info(f'process_folder_path = {process_folder_path}')
        pbs_id = run_post_process(process_folder_path, k_threshold, species_list)
        return pbs_id
        
    def __get_state(self, process_id, job_prefix):
        state = self.__job_manager.get_job_state(process_id, job_prefix)
        if state:
            return state
        logger.warning(f'process_id = {process_id}, job_prefix = {job_prefix} not in __job_manager')
        return None
        
    def get_kraken_job_state(self, process_id):
        return self.__get_state(process_id, kc.KRAKEN_JOB_PREFIX)
    
    def get_download_job_state(self, process_id):
        return self.__get_state(process_id, kc.KRAKEN_CUSTOM_DB_JOB_PREFIX)
        
    def get_postprocess_job_state(self, process_id):
        return self.__get_state(process_id, sc.POSTPROCESS_JOB_PREFIX)
    
    def add_kraken_process(self, process_id: str, email_address, db_type):
        logger.info(f'process_id = {process_id}')
        self.__job_manager.add_process(process_id, kc.KRAKEN_JOB_PREFIX, email_address, db_type)
    
    def add_download_process(self, process_id: str, email_address, species2download):
        logger.info(f'process_id = {process_id}')
        self.__job_manager.add_process(process_id, kc.KRAKEN_CUSTOM_DB_JOB_PREFIX, email_address, species2download)
    
    def add_postprocess(self, process_id: str, k_threshold, species_list):
        logger.info(f'process_id = {process_id}')
        self.__job_manager.add_process(process_id, sc.POSTPROCESS_JOB_PREFIX, k_threshold, species_list)
    
    def get_job_state(self, process_id: str, job_prefix: str):
        logger.info(f'process_id = {process_id} job_prefix = {job_prefix}')
        return self.__job_manager.get_job_state(process_id, job_prefix)
