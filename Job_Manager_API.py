import os
import shutil
import uuid
import pandas as pd
from InputValidator import InputValidator
from Job_Manager_Thread_Safe import Job_Manager_Thread_Safe
from utils import send_email, State, logger, LOGGER_LEVEL_JOB_MANAGE_API
from SharedConsts import K_MER_COUNTER_MATRIX_FILE_NAME, FINAL_OUTPUT_FILE_NAME, KRAKEN_JOB_PREFIX, POSTPROCESS_JOB_PREFIX
logger.setLevel(LOGGER_LEVEL_JOB_MANAGE_API)


class Job_Manager_API:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str, func2update_html):
        self.__input_file_name = input_file_name
        self.__upload_root_path = upload_root_path
        self.j_manager_thread_safe = Job_Manager_Thread_Safe(max_number_of_process, upload_root_path, input_file_name,
                                                             self.__process_state_changed, self.__process_state_changed)
        self.input_validator = InputValidator()
        self.__func2update_html = func2update_html

    def __build_and_send_mail(self, process_id, state, email_address):
        try:
            send_email('mxout.tau.ac.il', 'TAU BioSequence <bioSequence@tauex.tau.ac.il>',
                       email_address, subject=f'{process_id} process_id {state}.',
                       content=f'http://localhost:8000/process_state/{process_id}')
            logger.info(f'sent email to {email_address}')
        except:
            logger.exception(f'failed to sent email to {email_address}')

    def __process_state_changed(self, process_id, state, email_address):
        if state == State.Finished:
            if email_address != None:
                self.__build_and_send_mail(process_id, state, email_address)
        elif state == State.Crashed:
            self.__build_and_send_mail(process_id, state, 'elya.wygoda@gmail.com')
        self.__func2update_html(process_id, state)

    def __delete_folder(self, process_id):
        logger.info(f'process_id = {process_id}')
        folder2remove = os.path.join(self.__upload_root_path, process_id)
        shutil.rmtree(folder2remove)

    def __validate_input_file(self, process_id):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        if not os.path.isdir(parent_folder):
            logger.warning(f'process_id = {process_id} doen\'t have a dir')
            return False
        file2check = os.path.join(parent_folder, self.__input_file_name)
        if not os.path.isfile(file2check):
            file2check += '.gz' #maybe it is zipped
            if not os.path.isfile(file2check):
                logger.warning(f'process_id = {process_id} doen\'t have a file')
                return False
        if self.input_validator.validate_input_file(file2check):
            return True
        self.__delete_folder(process_id)
        logger.warning(f'validation failed {file2check}, deleting folder')
        return False
        
    def __validate_email_address(self, email_address):
        if len(email_address) > 100:
            return False
        if '@' in email_address and '.' in email_address:
            return True
        return False

    def get_new_process_id(self):
        return str(uuid.uuid4())

    def add_kraken_process(self, process_id: str, email_address: str):
        logger.info(f'process_id = {process_id} email_address = {email_address}')
        is_valid_file = self.__validate_input_file(process_id)
        is_valid_email = self.__validate_email_address(email_address)
        if is_valid_file and is_valid_email:
            logger.info(f'validated file and email address')
            self.j_manager_thread_safe.add_kraken_process(process_id, email_address)
            return True
        logger.warning(f'process_id = {process_id}, can\'t add process: is_valid_file = {is_valid_file} is_valid_email = {is_valid_email}')
        return False
        
    def add_postprocess(self, process_id: str, species_list: list, k_threshold: float):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        if os.path.isdir(parent_folder):
            self.j_manager_thread_safe.add_postprocess(process_id, k_threshold, species_list)
            return True
        logger.warning(f'process_id = {process_id} don\'t have a folder')
        return None
        
    def export_file(self, process_id: str):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        if os.path.isdir(parent_folder):
            file2return = os.path.join(parent_folder, FINAL_OUTPUT_FILE_NAME)
            if os.path.isfile(file2return):
                return file2return
        logger.warning(f'process_id = {process_id} doen\'t have a result file')
        return None
        
    def get_running_process(self):
        return self.j_manager_thread_safe.get_running_process()

    def get_waiting_process(self):
        return self.j_manager_thread_safe.get_waiting_process()

    def __get_state(self, process_id, job_prefix):
        state = self.j_manager_thread_safe.get_job_state(process_id, job_prefix)
        if state:
            return state
        logger.warning(f'process_id = {process_id}, job_prefix = {job_prefix} not in j_manager_thread_safe')
        return None
    
    def get_kraken_job_state(self, process_id):
        return self.__get_state(process_id, KRAKEN_JOB_PREFIX)
        
    def get_postprocess_job_state(self, process_id):
        return self.__get_state(process_id, POSTPROCESS_JOB_PREFIX)
        
    def get_UI_matrix(self, process_id):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        csv_UI_matrix = os.path.join(parent_folder, K_MER_COUNTER_MATRIX_FILE_NAME)
        if os.path.isfile(csv_UI_matrix):
            return pd.read_csv(csv_UI_matrix,index_col=0)
        logger.warning(f'process_id = {process_id} doen\'t have a result file')
        return None
