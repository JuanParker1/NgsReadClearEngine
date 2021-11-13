from threading import Lock
import uuid
from enum import Enum
from queue import Queue
import datetime
import os
from SearchEngine import SearchEngine
from apscheduler.schedulers.background import BackgroundScheduler
import JobListener
import SharedConsts as sc


class State(Enum):
    Running = 1
    Finshed = 2
    Crashed = 3
    Waiting = 4
    Init = 5
    

class Job_State:
    def __init__(self, folder_path: str, pbs_id: str):
        self.__folder_path = folder_path
        self.state = State.Init
        self.time_added = datetime.datetime.now()
        self.pbs_id = pbs_id
        
    def set_state(self, new_state: State):
        self.state = new_state

class Job_Manager_Thread_Safe:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str):
        self.max_number_of_process = max_number_of_process
        self.upload_root_path = upload_root_path
        self.__processes_state_dict = {}
        self.__mutex_processes_state_dict = Lock()
        self.__mutex_processes_waiting_queue = Lock()
        self.__waiting_queue = Queue()
        self.__search_engine = SearchEngine()
        self.__input_file_name = input_file_name
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
        
    
    def __p_long_running(self, a):
        print('Job_Manager_Thread_Safe', '__p_long_running()')
        #TODO handle
        pass
        
    def __p_running(self, process_id):
        print('Job_Manager_Thread_Safe', f'__p_running(process_id = {process_id})')
        self.__set_process_state(process_id, State.Running)
        
    def __p_error(self, process_id):
        print('Job_Manager_Thread_Safe', f'__p_error(process_id = {process_id})')
        self.__set_process_state(process_id, State.Crashed)
        process2add = self.__pop_from_waiting_queue()
        if process2add:
            self.add_process(process2add)
        
    def __p_Q(self, a):
        print('Job_Manager_Thread_Safe', f'__p_Q()')
        #TODO handle
        pass
    
    def __p_finished(self, a):
        print('Job_Manager_Thread_Safe', f'__p_finished()')
        self.__set_process_state(process_id, State.Finshed)
        process2add = self.__pop_from_waiting_queue()
        if process2add:
            self.add_process(process2add)
    
    def __set_process_state(self, process_id, state):
        self.__mutex_processes_state_dict.acquire()
        if process_id in self.__processes_state_dict:
            self.__processes_state_dict[process_id].set_state(state)
        else:
            #TODO handle
            print('Job_Manager_Thread_Safe', '__set_process_state()', f'process_id {process_id} not in dict state {state}')
        self.__mutex_processes_state_dict.release()
    
    def add_process(self, process_id: str):
        self.__mutex_processes_state_dict.acquire()
        
        if len(self.__processes_state_dict) < self.max_number_of_process:
            if process_id not in self.__processes_state_dict:
                process_folder_path = os.path.join(self.upload_root_path, process_id)
                file2fltr = os.path.join(process_folder_path, self.__input_file_name)
                pbs_id, _ = self.__search_engine.kraken_search(file2fltr, None)
                print('Job_Manager_Thread_Safe', 'add_process()', 'job submitted', f'pbs id {pbs_id}')
                self.__processes_state_dict[process_id] = Job_State(process_folder_path, pbs_id)
            else:
                # TODO handle exception
                print('add_process(): process id', process_id, 'already in processes_state_dict')
        else:
            # TODO handle
            print('Job_Manager_Thread_Safe', 'add_process()', 'too many processes, adding to wait list')
            self.__mutex_processes_waiting_queue.acquire()
            self.__waiting_queue.put(process_id)
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
        processes = list(self.__waiting_queue.queue)
        self.__mutex_processes_waiting_queue.release()
        return processes
        
    def __pop_from_waiting_queue(self):
        self.__mutex_processes_waiting_queue.acquire()
        process2return = None
        if self.__waiting_queue.qsize() > 0:
            process2return = self.__waiting_queue.get()
        self.__mutex_processes_waiting_queue.release()
        return process2return
    
    def get_job_state(self, process_id: str):
        if process_id in self.__processes_state_dict:
            return self.__processes_state_dict[process_id].state
        return None