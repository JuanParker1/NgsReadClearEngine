import uuid
from Job_Manager_Thread_Safe import Job_Manager_Thread_Safe
from Bio import SeqIO
import os
import shutil


class Job_Manager_API:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str):
        self.__input_file_name = input_file_name
        self.__upload_root_path = upload_root_path
        self.j_manager_thread_safe = Job_Manager_Thread_Safe(max_number_of_process, upload_root_path, input_file_name)
        
    
    def __is_fasta(self, filename):
        with open(filename, "r") as handle:
            fasta = SeqIO.parse(handle, "fasta")
            try : return any(fasta)
            
            except Exception as e:
                return False
            
    def __is_fastq(self, filename):
        with open(filename, "r") as handle:
            fastq = SeqIO.parse(handle, "fastq")
            
            try : return any(fastq)
            
            except Exception as e:
                return False
    
    def __delete_folder(self, process_id):
        folder2remove = os.path.join(self.__upload_root_path, process_id)
        shutil.rmtree(folder2remove)

    
    def __validate_input_file(self, process_id):
        parent_folder = os.path.join(self.__upload_root_path, process_id)
        file2check = os.path.join(parent_folder, self.__input_file_name)
        if self.__is_fasta(file2check):
            return True
        elif self.__is_fastq(file2check):
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
        
    def process_finished(self, process_id: str):
        self.j_manager_thread_safe.change_process_state_finished(process_id)
        process2add = self.j_manager_thread_safe.pop_from_waiting_queue()
        self.j_manager_thread_safe.add_process(process_id)


