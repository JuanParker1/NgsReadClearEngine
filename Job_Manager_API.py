import os
import shutil
import uuid
import pandas as pd
from InputValidator import InputValidator
from Job_Manager_Thread_Safe import Job_Manager_Thread_Safe
from utils import send_email, State, logger, LOGGER_LEVEL_JOB_MANAGE_API
from SharedConsts import K_MER_COUNTER_MATRIX_FILE_NAME
logger.setLevel(LOGGER_LEVEL_JOB_MANAGE_API)


class Job_Manager_API:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str, func2update_html):
        self.__input_file_name = input_file_name
        self.__upload_root_path = upload_root_path
        self.j_manager_thread_safe = Job_Manager_Thread_Safe(max_number_of_process, upload_root_path, input_file_name,
                                                             self.__process_state_changed)
        self.input_validator = InputValidator()
        self.func2update_html = func2update_html

    def __process_state_changed(self, process_id, state):
        if state == State.Finished:
            #TODO chane
            email_address = 'edodotan@mail.tau.ac.il'
            try:
                send_email('mxout.tau.ac.il', 'TAU BioSequence <bioSequence@tauex.tau.ac.il>',
                           email_address, subject=f'{process_id} process_id {state}.',
                           content=f'http://localhost:8000/process_state/{process_id}')
                logger.info(f'sent email to {email_address}')
            except:
                logger.exception(f'failed to sent email to {email_address}')
        self.func2update_html(process_id, state)

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
        if self.input_validator.validate_input_file(file2check):
            return True
        self.__delete_folder(process_id)
        logger.warning(f'validation failed {file2check}, deleting folder')
        return False

    def get_new_process_id(self):
        return str(uuid.uuid4())

    def add_process(self, process_id: str):
        logger.info(f'process_id = {process_id}')
        if self.__validate_input_file(process_id):
            self.j_manager_thread_safe.add_process(process_id)
            return True
        return False
        
    def export_file(self, process_id: str, species_list:list, k_threshold:float):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        csv_UI_matrix = os.path.join(parent_folder, K_MER_COUNTER_MATRIX_FILE_NAME)
        if os.path.isfile(csv_UI_matrix):
            return #TODO call postprocess with the species_list and k_threshold
        logger.warning(f'process_id = {process_id} doen\'t have a result file')
        return 'job unavialiable'
        
    def get_running_process(self):
        return self.j_manager_thread_safe.get_running_process()

    def get_waiting_process(self):
        return self.j_manager_thread_safe.get_waiting_process()

    def get_job_state(self, process_id):
        state = self.j_manager_thread_safe.get_job_state(process_id)
        if state:
            return state
        logger.warning(f'process_id = {process_id} not in j_manager_thread_safe')
        return 'job unavialiable'
        
    def get_UI_matrix(self, process_id):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        csv_UI_matrix = os.path.join(parent_folder, K_MER_COUNTER_MATRIX_FILE_NAME)
        if os.path.isfile(csv_UI_matrix):
            return pd.read_csv(csv_UI_matrix,index_col=0)
        logger.warning(f'process_id = {process_id} doen\'t have a result file')
        return 'job unavialiable'
