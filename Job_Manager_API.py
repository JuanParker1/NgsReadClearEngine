import os
import shutil
import uuid
import json
import pandas as pd
from InputValidator import InputValidator
from Job_Manager_Thread_Safe_GenomeFltr import Job_Manager_Thread_Safe_GenomeFltr
from utils import send_email, logger, LOGGER_LEVEL_JOB_MANAGE_API
from KrakenHandlers.KrakenConsts import KRAKEN_CUSTOM_DB_NAME_PREFIX
from SharedConsts import K_MER_COUNTER_MATRIX_FILE_NAME, \
    FINAL_OUTPUT_FILE_NAME, KRAKEN_SUMMARY_RESULTS_FOR_UI_FILE_NAME, EMAIL_CONSTS, UI_CONSTS, CUSTOM_DB_NAME, State
logger.setLevel(LOGGER_LEVEL_JOB_MANAGE_API)


class Job_Manager_API:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str, func2update_html):
        self.__input_file_name = input_file_name
        self.__upload_root_path = upload_root_path
        self.__j_manager = Job_Manager_Thread_Safe_GenomeFltr(max_number_of_process, upload_root_path, input_file_name, self.__update_download_process,
                                                             self.__process_state_changed, self.__process_state_changed)
        self.input_validator = InputValidator()
        self.__func2update_html = func2update_html

    def __build_and_send_mail(self, process_id, subject, content, email_address):
        try:
            send_email('mxout.tau.ac.il', 'TAU BioSequence <bioSequence@tauex.tau.ac.il>',
                       email_address, subject=subject,
                       content= content)
            logger.info(f'sent email to {email_address}')
        except:
            logger.exception(f'failed to sent email to {email_address}')
            
    def __update_download_process(self, process_id, state, email_address):
        logger.info(f'process_id = {process_id} state = {state}')
        if state == State.Finished:
            self.__j_manager.add_kraken_process(process_id, email_address, KRAKEN_CUSTOM_DB_NAME_PREFIX + process_id)
        self.__func2update_html(process_id, state)

    def __process_state_changed(self, process_id, state, email_address):
        if state == State.Finished:
            if email_address != None:
                self.__build_and_send_mail(process_id, EMAIL_CONSTS.FINISHED_TITLE, EMAIL_CONSTS.FINISHED_CONTENT.format(process_id=process_id), email_address)
        elif state == State.Crashed:
            if email_address != None:
                self.__build_and_send_mail(process_id, EMAIL_CONSTS.CRASHED_TITLE, EMAIL_CONSTS.CRASHED_CONTENT.format(process_id=process_id), email_address)
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

    def add_kraken_process(self, process_id: str, email_address: str, db_type: str, species2download: list):
        logger.info(f'process_id = {process_id} email_address = {email_address} db_type = {db_type} species2download = {species2download}')
        is_valid_file = self.__validate_input_file(process_id)
        is_valid_email = self.__validate_email_address(email_address)
        if is_valid_file and is_valid_email:
            logger.info(f'validated file and email address')
            if db_type == CUSTOM_DB_NAME:
                self.__j_manager.add_download_process(process_id, email_address, species2download)
                self.__build_and_send_mail(process_id, EMAIL_CONSTS.SUBMITTED_TITLE, EMAIL_CONSTS.SUBMITTED_CONTENT.format(process_id=process_id), email_address)
                return True
            self.__j_manager.add_kraken_process(process_id, email_address, db_type)
            self.__build_and_send_mail(process_id, EMAIL_CONSTS.SUBMITTED_TITLE, EMAIL_CONSTS.SUBMITTED_CONTENT.format(process_id=process_id), email_address)
            return True
        logger.warning(f'process_id = {process_id}, can\'t add process: is_valid_file = {is_valid_file} is_valid_email = {is_valid_email}')
        return False
        
    def add_postprocess(self, process_id: str, species_list: list, k_threshold: float):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        if os.path.isdir(parent_folder):
            self.__j_manager.add_postprocess(process_id, k_threshold, species_list)
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
    
    def get_kraken_job_state(self, process_id):
        return self.__j_manager.get_kraken_job_state(process_id)
    
    def get_download_job_state(self, process_id):
        return self.__j_manager.get_download_job_state(process_id)
    
    def get_postprocess_job_state(self, process_id):
        return self.__j_manager.get_postprocess_job_state(process_id)
        
    def get_UI_matrix(self, process_id):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        csv_UI_matrix_path = os.path.join(parent_folder, K_MER_COUNTER_MATRIX_FILE_NAME)
        summary_stats_json_path = os.path.join(parent_folder, KRAKEN_SUMMARY_RESULTS_FOR_UI_FILE_NAME)
        df2return = None
        json2return = None
        if os.path.isfile(csv_UI_matrix_path):
            df2return = pd.read_csv(csv_UI_matrix_path,index_col=0)
            columns = df2return.columns
            new_columns = {column:column.replace("'","") for column in columns} #columns names cannot have ' inside - causes bugs in HTML
            df2return.rename(columns=new_columns, inplace=True)
        if os.path.isfile(summary_stats_json_path):
            json2return = json.load(open(summary_stats_json_path))
        
        logger.info(f'process_id = {process_id} df2return = {df2return} json2return = {json2return}')
        return df2return, json2return
        
    def parse_form_inputs(self, form_dict: dict):
        email_address = form_dict.get('email', None)
        db_type = form_dict.get('db', CUSTOM_DB_NAME)
        species_list = []
        if db_type == CUSTOM_DB_NAME:
            for i in range(UI_CONSTS.KRAKEN_MAX_CUSTOM_SPECIES):
                species_input = form_dict.get(UI_CONSTS.SPECIES_FORM_PREFIX + str(i), '')
                if species_input != '':
                    species_list.append(species_input)
        return email_address, db_type, species_list
        
    def valid_species_list(self, species_list: list):
        for species in species_list:
            if not self.input_validator.valid_species(species):
                return False
        return True

    def clean_internal_state(self):
        self.__j_manager.clean_internal_state()