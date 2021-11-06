import uuid
from Job_Manager_Thread_Safe import Job_Manager_Thread_Safe
import os
import shutil
from InputValidator import InputValidator


class Job_Manager_API:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str):
        self.__input_file_name = input_file_name
        self.__upload_root_path = upload_root_path
        self.j_manager_thread_safe = Job_Manager_Thread_Safe(max_number_of_process, upload_root_path, input_file_name)
        self.input_validator = InputValidator()
    
    def __delete_folder(self, process_id):
        folder2remove = os.path.join(self.__upload_root_path, process_id)
        shutil.rmtree(folder2remove)
    
    def __validate_input_file(self, process_id):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        if not os.path.isdir(parent_folder):
            print('Job_Manager_API', '__validate_input_file', f'no folder of {process_id}')
            return False
        file2check = os.path.join(parent_folder, self.__input_file_name)
        if self.input_validator.validate_input_file(file2check):
            return True
        self.__delete_folder(process_id)
        return False
    
    def get_new_process_id(self):
        return str(uuid.uuid4())
        
    def add_process(self, process_id: str):
        if self.__validate_input_file(process_id):
            self.j_manager_thread_safe.add_process(process_id)
            return True
        return False
        
    def get_running_process(self):
        return self.j_manager_thread_safe.get_running_process()
        
    def get_waiting_process(self):
        return self.j_manager_thread_safe.get_waiting_process()
        
    def get_job_state(self, process_id):
        state = self.j_manager_thread_safe.get_job_state(process_id)
        if state:
            return state
        return 'job unavialiable'


