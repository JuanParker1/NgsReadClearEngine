from threading import Lock
import uuid
import datetime
import os
from SearchEngine import SearchEngine
from apscheduler.schedulers.background import BackgroundScheduler
import JobListener
import SharedConsts as sc
from utils import State


class Job_State:
    def __init__(self, folder_path: str, pbs_id: str):
        self.__folder_path = folder_path
        self.state = State.Init
        self.time_added = datetime.datetime.now()
        self.pbs_id = pbs_id
        
    def set_state(self, new_state: State):
        self.state = new_state

class Job_Manager_Thread_Safe:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str, func2update_html):
        self.max_number_of_process = max_number_of_process
        self.upload_root_path = upload_root_path
        self.__processes_state_dict = {}
        self.__mutex_processes_state_dict = Lock()
        self.__mutex_processes_waiting_queue = Lock()
        self.__waiting_list = []
        self.__search_engine = SearchEngine()
        self.__input_file_name = input_file_name
        self.__func2update_html = func2update_html
        function_to_call = {
            sc.LONG_RUNNING_JOBS_NAME: self.__p_long_running,
            sc.NEW_RUNNING_JOBS_NAME: self.__p_running,
            sc.QUEUE_JOBS_NAME: self.__p_Q,
            sc.FINISHED_JOBS_NAME: self.__p_finished,
            sc.ERROR_JOBS_NAME: self.__p_error
        }
        self.__listener = JobListener.PbsListener(function_to_call)
        self.__scheduler = BackgroundScheduler()
        self.__scheduler.add_job(self.__listener.run, 'interval', seconds=5)
        self.__scheduler.start()      
        
    def __calc_num_running_processes(self):
        running_processes = 0
        self.__mutex_processes_state_dict.acquire()
        
        for process_id in self.__processes_state_dict:
            if self.__processes_state_dict[process_id].state == State.Running:
                running_processes += 1
        
        self.__mutex_processes_state_dict.release()
        return running_processes
    
    def __calc_process_id(self, pbs_id):
        clean_pbs_id = pbs_id.split('.')[0]
        process_id2return = None
        self.__mutex_processes_state_dict.acquire()
        for process_id in self.__processes_state_dict:
            if clean_pbs_id == self.__processes_state_dict[process_id].pbs_id:
                process_id2return = process_id
                break
        self.__mutex_processes_state_dict.release()
        if not process_id2return:
            #TODO handle
            print('Job_Manager_Thread_Safe', f'__calc_process_id(pbs_id = {pbs_id})', f'process not found in dict = {self.__processes_state_dict}')
        return process_id2return
    
    def __p_long_running(self, pbs_id):
        print('Job_Manager_Thread_Safe', '__p_long_running()')
        #TODO handle
        pass
        
    def __p_running(self, pbs_id):
        process_id = self.__calc_process_id(pbs_id)
        print('Job_Manager_Thread_Safe', f'__p_running(pbs_id = {pbs_id}) process_id = {process_id}')
        self.__set_process_state(process_id, State.Running)
        
    def __p_error(self, pbs_id):
        process_id = self.__calc_process_id(pbs_id)
        print('Job_Manager_Thread_Safe', f'__p_error(process_id = {process_id})')
        self.__set_process_state(process_id, State.Crashed)
        process2add = self.__pop_from_waiting_queue()
        if process2add:
            self.add_process(process2add)
        
    def __p_Q(self, pbs_id):
        print('Job_Manager_Thread_Safe', f'__p_Q()')
        #TODO handle
        pass
    
    def __p_finished(self, pbs_id):
        process_id = self.__calc_process_id(pbs_id)
        print('Job_Manager_Thread_Safe', f'__p_finished(pbs_id = {pbs_id})')
        self.__set_process_state(process_id, State.Finished)
        process2add = self.__pop_from_waiting_queue()
        print('Job_Manager_Thread_Safe', f'__p_finished', f'process2add = {process2add}')
        if process2add:
            self.add_process(process2add)
    
    def __set_process_state(self, process_id, state):
        print('Job_Manager_Thread_Safe', f'__set_process_state(process_id = {process_id} state = {state})')
        self.__mutex_processes_state_dict.acquire()
        if process_id in self.__processes_state_dict:
            self.__processes_state_dict[process_id].set_state(state)
        else:
            #TODO handle
            print('Job_Manager_Thread_Safe', '__set_process_state()', f'process_id {process_id} not in dict state {state}')
            print('Job_Manager_Thread_Safe', '__set_process_state()', f'self.__processes_state_dict = {self.__processes_state_dict}')
        self.__mutex_processes_state_dict.release()
        print('Job_Manager_Thread_Safe', f'__set_process_state calling __func2update_html')
        self.__func2update_html(process_id, state)
    
    def add_process(self, process_id: str):
        # don't put inside the mutex area - the funciton acquire the mutex too
        running_processes = self.__calc_num_running_processes()
        self.__mutex_processes_state_dict.acquire()
        
        if running_processes <= self.max_number_of_process:
            if process_id not in self.__processes_state_dict:
                process_folder_path = os.path.join(self.upload_root_path, process_id)
                file2fltr = os.path.join(process_folder_path, self.__input_file_name)
                print('Job_Manager_Thread_Safe', '--before add_process()--')
                pbs_id, _ = self.__search_engine.kraken_search(file2fltr, None)
                print('Job_Manager_Thread_Safe', '--add_process()--', 'job submitted', f'pbs id {pbs_id}')
                self.__processes_state_dict[process_id] = Job_State(process_folder_path, pbs_id)
            else:
                # TODO handle exception
                print('add_process(): process id', process_id, 'already in processes_state_dict')
        else:
            # TODO handle
            print('Job_Manager_Thread_Safe', 'add_process()', 'too many processes, adding to wait list')
            self.__mutex_processes_waiting_queue.acquire()
            self.__waiting_list.append(process_id)
            self.__mutex_processes_waiting_queue.release()
        
        self.__mutex_processes_state_dict.release()
        
    def get_running_process(self):
        self.__mutex_processes_state_dict.acquire()
        values2return = []
        for key in self.__processes_state_dict.keys():
            values2return.append((key, self.__processes_state_dict[key].state))
        self.__mutex_processes_state_dict.release()
        return values2return
        
    def get_waiting_process(self):
        self.__mutex_processes_waiting_queue.acquire()
        processes = self.__waiting_list
        self.__mutex_processes_waiting_queue.release()
        return processes
        
    def __pop_from_waiting_queue(self):
        self.__mutex_processes_waiting_queue.acquire()
        process2return = None
        if len(self.__waiting_list) > 0:
            process2return = self.__waiting_list.pop(0)
        self.__mutex_processes_waiting_queue.release()
        return process2return
    
    def get_job_state(self, process_id: str):
        if process_id in self.__processes_state_dict:
            return self.__processes_state_dict[process_id].state
        if process_id in self.__waiting_list:
            return State.Waiting
        return None