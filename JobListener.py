import subprocess
import re
import pandas as pd
from SharedConsts import QstatDataColumns, SRVER_USERNAME, KRAKEN_JOB_PREFIX, JOB_CHANGE_COLS, JOB_ELAPSED_TIME, \
    JOB_RUNNING_TIME_LIMIT_IN_HOURS, JOB_NUMBER_COL, LONG_RUNNING_JOBS_NAME, QUEUE_JOBS_NAME, NEW_RUNNING_JOBS_NAME, \
    FINISHED_JOBS_NAME, JOB_STATUS_COL, WEIRD_BEHAVIOR_JOB_TO_CHECK, FINISHED_JOBS_ERROR
import asyncio


class PbsListener:

    def __init__(self, functions_to_call):
        self.functions = functions_to_call
        self.previous_state = None

    async def run(self, sleep_in_sec):
        while True:
            # get running jobs data
            current_job_state = await self.get_server_job_stats()
            # check state diff, act accordingly
            await self.handle_job_state(current_job_state)
            # update job status
            self.previous_state = current_job_state
            # wait till next heartbeat
            await asyncio.sleep(sleep_in_sec)

    async def handle_job_state(self, new_job_state):
        """
        this function gets the newly sampled PBS job status and alerts the job manager accordingly through the
        "functions_to_call" dictionary that is provided by the job manager upon creation.
        :param new_job_state: newly sampled job state
        """
        # todo: talk with everyone of the case of jobs stuck in Q
        # check for long running jobs:
        await self.handle_long_running_jobs(new_job_state)

        # find jobs who have changed status and act accordingly
        changed_jobs = await self.get_changed_job_state(new_job_state)
        for job_row, index in changed_jobs.iterrows():
            job_number = job_row[JOB_NUMBER_COL]
            job_status = job_row[JOB_STATUS_COL]
            # case of running jobs
            if job_status == 'R':
                # case where job finished
                if job_row['origin'] == 'P':
                    self.functions[FINISHED_JOBS_NAME](job_number)
                # case of newly running job
                elif job_row['origin'] == 'N':
                    self.functions[NEW_RUNNING_JOBS_NAME](job_number)
                else:
                    self.functions[WEIRD_BEHAVIOR_JOB_TO_CHECK](job_number)
            elif job_status == 'Q':
                self.functions[QUEUE_JOBS_NAME](job_number)
            elif job_status == 'E':
                self.functions[FINISHED_JOBS_ERROR](job_number)
            else:
                self.functions[WEIRD_BEHAVIOR_JOB_TO_CHECK](job_number)

    async def get_server_job_stats(self):
        """
        gets the users current job statistics (running and queued) and parses them
        :return: a data frame of all current jobs
        """
        result = subprocess.run(['qstat', f'-u {SRVER_USERNAME}'], stdout=subprocess.PIPE)
        result_lines = (str(result.stdout).split('\\n'))[5:-1]  # irrelevant text from qstat
        results_params = [re.sub('\s+', ' ', x).split(' ') for x in result_lines]  # remove spaces and turn to data
        results_df = pd.DataFrame(results_params, columns=QstatDataColumns)
        results_df['cpus'] = results_df['cpus'].astype(int)
        results_df = results_df[results_df['job_name'].str.startswith(KRAKEN_JOB_PREFIX)]

        return results_df

    async def get_changed_job_state(self, current_job_state):
        """
        takes the new job state and returns a pandas DF with only the relevant job data,
        it does so by removing all jobs that appear with the same status in both of the states (previous, current)
        it does NOT handle long running jobs.
        :param current_job_state: the newly sampled job state
        :return: a pandas df with jobs that have a different status in new sampled data than the previous
        (including new jobs)
        """
        if self.previous_state is None:
            return current_job_state[JOB_CHANGE_COLS]
        temp_df = self.previous_state
        temp_df['origin'] = 'P'
        current_job_state['origin'] = 'N'
        temp_df = temp_df.append(current_job_state)
        return temp_df.drop_duplicates(keep=False)

    async def handle_long_running_jobs(self, current_job_state):
        """
        handles jobs that have exceeded the timeout
        :param current_job_state: newly sampled job state
        """
        # todo: discuss if we want to kill these jobs from here or not.
        temp_new_job_state = current_job_state
        temp_new_job_state = temp_new_job_state[JOB_ELAPSED_TIME].astype(str)
        temp_new_job_state[JOB_ELAPSED_TIME] = temp_new_job_state[JOB_ELAPSED_TIME].str.split(':')  # just care about the hours
        temp_new_job_state[JOB_ELAPSED_TIME] = temp_new_job_state[JOB_ELAPSED_TIME].apply(lambda x: int(x[0]))
        long_running_jobs = temp_new_job_state[temp_new_job_state[JOB_ELAPSED_TIME] >= JOB_RUNNING_TIME_LIMIT_IN_HOURS][
            JOB_NUMBER_COL].values
        for long_running_job in long_running_jobs:
            self.functions[LONG_RUNNING_JOBS_NAME](long_running_job)
