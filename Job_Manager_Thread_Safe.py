import datetime
import os
from threading import Lock
from apscheduler.schedulers.background import BackgroundScheduler
from JobListener import PbsListener
import SharedConsts as sc
from KrakenHandlers.SearchEngine import SearchEngine
from KrakenHandlers.SearchResultAnalyzer import run_post_process
from utils import State, logger, LOGGER_LEVEL_JOB_MANAGE_THREAD_SAFE
logger.setLevel(LOGGER_LEVEL_JOB_MANAGE_THREAD_SAFE)

JOBS_PREFIXES_LST = [sc.KRAKEN_JOB_PREFIX, sc.POSTPROCESS_JOB_PREFIX]

class Job_State:
    def __init__(self, folder_path: str, email_address: str):
        self.__folder_path = folder_path
        self.__job_states_dict = {prefix: None for prefix in JOBS_PREFIXES_LST}
        self.__time_added = datetime.datetime.now()
        self.__pbs_id_dict = {prefix: None for prefix in JOBS_PREFIXES_LST}
        self.__email_address = email_address

    def set_job_state(self, new_state: State, job_prefix: str):
        if job_prefix in self.__job_states_dict:
            self.__job_states_dict[job_prefix] = new_state
        else:
            logger.error(f'job_prefix = {job_prefix} not in self.__job_states_dict = {self.__job_states_dict}')
        
    def get_job_state(self, job_prefix: str):
        if job_prefix in self.__job_states_dict:
            return self.__job_states_dict[job_prefix]
        else:
            logger.error(f'job_prefix = {job_prefix} not in self.__job_states_dict = {self.__job_states_dict}')
        
    def set_pbs_id(self, pbs_id: str, job_prefix: str):
        if job_prefix in self.__job_states_dict:
            self.__pbs_id_dict[job_prefix] = pbs_id
        else:
            logger.error(f'job_prefix = {job_prefix} not in self.__pbs_id_dict = {self.__pbs_id_dict}')
        
    def get_pbs_id(self, job_prefix: str):
        if job_prefix in self.__pbs_id_dict:
            return self.__pbs_id_dict[job_prefix]
        else:
            logger.error(f'job_prefix = {job_prefix} not in self.__pbs_id_dict = {self.__pbs_id_dict}')
        
    def get_email_address(self):
        return self.__email_address

class Job_Manager_Thread_Safe:
    def __init__(self, max_number_of_process: int, upload_root_path: str, input_file_name: str, func2update_html_kraken, func2update_html_postprocess):
        self.max_number_of_process = max_number_of_process
        self.__upload_root_path = upload_root_path
        self.__processes_state_dict = {}
        self.__mutex_processes_state_dict = Lock()
        self.__mutex_processes_waiting_queue = Lock()
        self.__waiting_list = []
        self.__search_engine = SearchEngine()
        self.__input_file_name = input_file_name
        self.__func2update_html_kraken = func2update_html_kraken
        self.__func2update_html_postprocess = func2update_html_postprocess
        function_to_call_listener = {
            sc.KRAKEN_JOB_PREFIX: self.__make_function_dict4listener(lambda process_id, state: self.__set_process_state(process_id, state, sc.KRAKEN_JOB_PREFIX, self.__func2update_html_kraken)),
            sc.POSTPROCESS_JOB_PREFIX: self.__make_function_dict4listener(lambda process_id, state: self.__set_process_state(process_id, state, sc.POSTPROCESS_JOB_PREFIX, self.__func2update_html_postprocess)),
        }
        assert len(function_to_call_listener) == len(JOBS_PREFIXES_LST), f'verify all prefixes jobs are in function_to_call_listener'
        self.job_prefixes_to_function_append_job = {
            sc.KRAKEN_JOB_PREFIX: self.add_kraken_process,
            sc.POSTPROCESS_JOB_PREFIX: self.add_postprocess,
        }
        assert len(self.job_prefixes_to_function_append_job) == len(JOBS_PREFIXES_LST), f'verify all prefixes jobs are in self.job_prefixes_to_function_append_job'
        # create listener on queue
        self.__listener = PbsListener(function_to_call_listener)
        self.__scheduler = BackgroundScheduler()
        self.__scheduler.add_job(self.__listener.run, 'interval', seconds=5)
        self.__scheduler.start()

    def __calc_num_running_processes(self):
        running_processes = 0
        self.__mutex_processes_state_dict.acquire()
        for process_id in self.__processes_state_dict:
            for job_prefix in JOBS_PREFIXES_LST:
                if self.__processes_state_dict[process_id].get_job_state(job_prefix) == State.Running:
                    running_processes += 1
        self.__mutex_processes_state_dict.release()
        return running_processes

    def __calc_process_id(self, pbs_id):
        clean_pbs_id = pbs_id.split('.')[0]
        process_id2return = None
        self.__mutex_processes_state_dict.acquire()
        for process_id in self.__processes_state_dict:
            for job_prefix in JOBS_PREFIXES_LST:
                if clean_pbs_id == self.__processes_state_dict[process_id].get_pbs_id(job_prefix):
                    process_id2return = process_id
                    break
        self.__mutex_processes_state_dict.release()
        if not process_id2return:
            logger.warning(f'clean_pbs_id = {clean_pbs_id} not in __processes_state_dict')
        return process_id2return

    def __log_and_set_change(self, pbs_id, set_process_state_func, state):
        process_id = self.__calc_process_id(pbs_id)
        logger.info(f'pbs_id = {pbs_id}  process_id = {process_id} state is {state}')
        set_process_state_func(process_id, state)

    def __make_function_dict4listener(self, set_process_state):
        return {
            sc.LONG_RUNNING_JOBS_NAME: lambda x: self.__log_and_set_change(x, set_process_state, State.Running), #TODO handle -currently same behevior as running
            sc.NEW_RUNNING_JOBS_NAME: lambda x: self.__log_and_set_change(x, set_process_state, State.Running),
            sc.QUEUE_JOBS_NAME: lambda x: self.__log_and_set_change(x, set_process_state, State.Queue),
            sc.FINISHED_JOBS_NAME: lambda x: self.__log_and_set_change(x, set_process_state, State.Finished),
            sc.ERROR_JOBS_NAME: lambda x: self.__log_and_set_change(x, set_process_state, State.Crashed),
        }

    def __set_process_state(self, process_id, state, job_prefix, func2update):
        logger.info(f'process_id = {process_id}, state = {state}')
        email_address = None
        self.__mutex_processes_state_dict.acquire()
        if process_id in self.__processes_state_dict:
            self.__processes_state_dict[process_id].set_job_state(state, job_prefix)
            email_address = self.__processes_state_dict[process_id].get_email_address()
        else:
            # TODO handle
            logger.warning(f'process_id {process_id} not in __processes_state_dict: {self.__processes_state_dict}')
        self.__mutex_processes_state_dict.release()
        
        # don't put inside the mutex area - the funciton acquire the mutex too
        if state == State.Finished or state == State.Crashed:
            self.__add_process_from_waiting_list()
        func2update(process_id, state, email_address)

    def __add_process_from_waiting_list(self):
        process2add, job_type, running_arguments = self.__pop_from_waiting_queue()
        if process2add:
            logger.debug(f'adding new process after processed finished process2add = {process2add} job_type = {job_type}')
            if job_type in self.job_prefixes_to_function_append_job:
                logger.debug(f'calling function to: {self.job_prefixes_to_function_append_job[job_type]}({process2add}, {running_arguments})')
                self.job_prefixes_to_function_append_job[job_type](process2add, *running_arguments)
            else:
                logger.error(f'job_type = {job_type} unregocnized in {self.job_prefixes_to_function_append_job}')

    def add_kraken_process(self, process_id: str, email_address):
        logger.info(f'process_id = {process_id}, email_address = {email_address}')
        # don't put inside the mutex area - the funciton acquire the mutex too
        running_processes = self.__calc_num_running_processes()
        self.__mutex_processes_state_dict.acquire()
        if running_processes < self.max_number_of_process:
            if process_id not in self.__processes_state_dict:
                process_folder_path = os.path.join(self.__upload_root_path, process_id)
                file2fltr = os.path.join(process_folder_path, self.__input_file_name)
                pbs_id, _ = self.__search_engine.kraken_search(file2fltr, None)
                logger.debug(f'process_id = {process_id} kraken process started, pbs_id = {pbs_id}')
                self.__processes_state_dict[process_id] = Job_State(process_folder_path, email_address)
                self.__processes_state_dict[process_id].set_job_state(State.Init, sc.KRAKEN_JOB_PREFIX)
                self.__processes_state_dict[process_id].set_pbs_id(pbs_id, sc.KRAKEN_JOB_PREFIX)
            else:
                # TODO handle exception
                logger.error('already in processes_state_dict')
        else:
            logger.info(f'process_id = {process_id} adding to waiting list')
            self.__mutex_processes_waiting_queue.acquire()
            self.__waiting_list.append((process_id, sc.KRAKEN_JOB_PREFIX, [email_address]))
            self.__mutex_processes_waiting_queue.release()
            
        self.__mutex_processes_state_dict.release()
    
    def add_postprocess(self, process_id: str, k_threshold, species_list):
        logger.info(f'process_id = {process_id}, k_threshold = {k_threshold}, species_list = {species_list}')
        # don't put inside the mutex area - the funciton acquire the mutex too
        running_processes = self.__calc_num_running_processes()
        self.__mutex_processes_state_dict.acquire()
        if running_processes < self.max_number_of_process:
            if process_id in self.__processes_state_dict:
                parent_folder = os.path.join(self.__upload_root_path, process_id)
                pbs_id = run_post_process(parent_folder, k_threshold, species_list)
                logger.debug(f'process_id = {process_id} postprocess process started, pbs_id = {pbs_id}')
                self.__processes_state_dict[process_id].set_job_state(State.Init, sc.POSTPROCESS_JOB_PREFIX)
                self.__processes_state_dict[process_id].set_pbs_id(pbs_id, sc.POSTPROCESS_JOB_PREFIX)
            else:
                # TODO handle exception
                logger.error(f'trying to add postprocess when process_id = {process_id} not in self.__processes_state_dict')
        else:
            logger.info(f'process_id = {process_id} adding to waiting list')
            self.__mutex_processes_waiting_queue.acquire()
            self.__waiting_list.append((process_id, sc.POSTPROCESS_JOB_PREFIX, (k_threshold, species_list)))
            self.__mutex_processes_waiting_queue.release()
            
        self.__mutex_processes_state_dict.release()

    def get_running_process(self):
        self.__mutex_processes_state_dict.acquire()
        values2return = []
        for key in self.__processes_state_dict.keys():
            values2return.append((key, self.__processes_state_dict[key].get_job_state(sc.KRAKEN_JOB_PREFIX)))
        self.__mutex_processes_state_dict.release()
        return values2return

    def get_waiting_process(self):
        self.__mutex_processes_waiting_queue.acquire()
        processes = self.__waiting_list
        self.__mutex_processes_waiting_queue.release()
        return processes

    def __pop_from_waiting_queue(self):
        self.__mutex_processes_waiting_queue.acquire()
        process_tuple2return = None, None, None
        if len(self.__waiting_list) > 0:
            process_tuple2return = self.__waiting_list.pop(0)
        self.__mutex_processes_waiting_queue.release()
        logger.info(f'process2return = {process_tuple2return}')
        return process_tuple2return

    def get_job_state(self, process_id: str, job_prefix: str):
        state2return = None
        if process_id in self.__processes_state_dict:
            state2return = self.__processes_state_dict[process_id].get_job_state(job_prefix)
        self.__mutex_processes_waiting_queue.acquire()
        for process_tuple in self.__waiting_list:
            if process_id in process_tuple:
                state2return = State.Waiting
                break
        self.__mutex_processes_waiting_queue.release()
        logger.info(f'state2return = {state2return}')
        return state2return