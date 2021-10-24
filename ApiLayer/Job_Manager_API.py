import uuid
from Job_Manager_Thread_Safe import Job_Manager_Thread_Safe


class Job_Manager_API:
    def __init__(self, max_number_of_process: int, upload_root_path: str):
        self.j_manager_thread_safe = Job_Manager_Thread_Safe(max_number_of_process, upload_root_path)
        
    def get_new_process_id(self):
        return str(uuid.uuid4())
        
    def add_process(self, process_id: str):
        self.j_manager_thread_safe.add_process(process_id)
        
    def get_running_process(self):
        return self.j_manager_thread_safe.get_running_process()
        
    def get_waiting_process(self):
        return self.j_manager_thread_safe.get_waiting_process()
        
    def process_finished(self, process_id: str):
        self.j_manager_thread_safe.change_process_state_finished(process_id)
        process2add = self.j_manager_thread_safe.pop_from_waiting_queue()
        self.j_manager_thread_safe.add_process(process_id)


