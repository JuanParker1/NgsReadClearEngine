import datetime
import os
from threading import Lock
from apscheduler.schedulers.background import BackgroundScheduler
import JobListener
import SharedConsts as sc
from KrakenHandlers.SearchEngine import SearchEngine
from utils import State, logger, LOGGER_LEVEL_JOB_MANAGE_THREAD_SAFE
logger.setLevel(LOGGER_LEVEL_JOB_MANAGE_THREAD_SAFE)


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
            logger.warning(f'clean_pbs_id = {clean_pbs_id} not in __processes_state_dict')
        return process_id2return

    def __p_long_running(self, pbs_id):
        logger.warning(f'pbs_id = {pbs_id}')
        # TODO handle
        pass

    def __p_running(self, pbs_id):
        process_id = self.__calc_process_id(pbs_id)
        logger.info(f'pbs_id = {pbs_id} process_id = {process_id}')
        self.__set_process_state(process_id, State.Running)

    def __p_error(self, pbs_id):
        process_id = self.__calc_process_id(pbs_id)
        logger.warning(f'pbs_id = {pbs_id} process_id = {process_id}')
        self.__set_process_state(process_id, State.Crashed)
        process2add = self.__pop_from_waiting_queue()
        if process2add:
            self.add_process(process2add)

    def __p_Q(self, pbs_id):
        logger.warning(f'pbs_id = {pbs_id}')
        # TODO handle
        pass

    def __p_finished(self, pbs_id):
        process_id = self.__calc_process_id(pbs_id)
        logger.info(f'pbs_id = {pbs_id} process_id = {process_id}')
        self.__set_process_state(process_id, State.Finished)
        process2add = self.__pop_from_waiting_queue()
        if process2add:
            logger.debug(f'adding new process after processed finished')
            self.add_process(process2add)

    def __set_process_state(self, process_id, state):
        logger.info(f'process_id = {process_id}, state = {state}')
        self.__mutex_processes_state_dict.acquire()
        if process_id in self.__processes_state_dict:
            self.__processes_state_dict[process_id].set_state(state)
        else:
            # TODO handle
            logger.warning(f'process_id {process_id} not in __processes_state_dict: {__processes_state_dict}')
        self.__mutex_processes_state_dict.release()
        self.__func2update_html(process_id, state)

    def add_process(self, process_id: str):
        # don't put inside the mutex area - the funciton acquire the mutex too
        running_processes = self.__calc_num_running_processes()
        self.__mutex_processes_state_dict.acquire()
        if running_processes < self.max_number_of_process:
            if process_id not in self.__processes_state_dict:
                process_folder_path = os.path.join(self.upload_root_path, process_id)
                file2fltr = os.path.join(process_folder_path, self.__input_file_name)
                pbs_id, _ = self.__search_engine.kraken_search(file2fltr, None)
                logger.debug(f'process_id = {process_id} kraken process started, pbs_id = {pbs_id}')
                self.__processes_state_dict[process_id] = Job_State(process_folder_path, pbs_id)
            else:
                # TODO handle exception
                logger.error('already in processes_state_dict')
        else:
            logger.info(f'process_id = {process_id} adding to waiting list')
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
        logger.info(f'process2return = {process2return}')
        return process2return

    def get_job_state(self, process_id: str):
        state2return = None
        if process_id in self.__processes_state_dict:
            state2return = self.__processes_state_dict[process_id].state
        if process_id in self.__waiting_list:
            state2return = State.Waiting
        logger.info(f'state2return = {state2return}')
        return state2return
