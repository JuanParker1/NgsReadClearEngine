from threading import Lock
import uuid
from enum import Enum
from queue import Queue
import datetime
import os
from SearchEngine import SearchEngine


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
        self.listener = []
        
    def add_process(self, process_id: str):
        self.__mutex_processes_state_dict.acquire()
        
        if len(self.__processes_state_dict) < self.max_number_of_process:
            if process_id not in self.__processes_state_dict:
                process_folder_path = os.path.join(self.upload_root_path, process_id)
                file2fltr = os.path.join(process_folder_path, self.__input_file_name)
                pbs_id, _ = self.__search_engine.kraken_search(file2fltr, None)
                self.__processes_state_dict[process_id] = Job_State(process_folder_path, pbs_id)
            else:
                # TODO handle exception
                print('add_process(): process id', process_id, 'already in processes_state_dict')
        else:
            # TODO handle
            print('too many processes, adding to wait list')
            self.__mutex_processes_waiting_queue.acquire()
            self.__waiting_queue.put(process_id)
            self.__mutex_processes_waiting_queue.release()
        
        self.__mutex_processes_state_dict.release()
        
    def get_running_process(self):
        self.__mutex_processes_state_dict.acquire()
        keys = self.__processes_state_dict.keys()
        self.__mutex_processes_state_dict.release()
        return keys
        
    def get_waiting_process(self):
        self.__mutex_processes_waiting_queue.acquire()
        processes = list(self.__waiting_queue.queue)
        self.__mutex_processes_waiting_queue.release()
        return processes
        
    def change_process_state_finished(self, process_id: str):
        self.__mutex_processes_state_dict.acquire()
        
        if process_id in self.__processes_state_dict:
            self.__processes_state_dict[process_id].set_state(State.Finshed)
            
        else:
            #TODO handle exception
            print('process_finished(): process id', process_id, 'not in processes_state_dict')
            
        self.__mutex_processes_state_dict.release()
        
    def pop_from_waiting_queue(self):
        self.__mutex_processes_waiting_queue.acquire()
        process2return = None
        if self.__waiting_queue.qsize() > 0:
            process2return = self.__waiting_queue.get()
        self.__mutex_processes_waiting_queue.release()
        return process2return


