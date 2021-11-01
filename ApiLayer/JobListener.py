import subprocess
import re
import pandas as pd
from SharedConsts import QstatDataColumns, SRVER_USERNAME, KRAKEN_JOB_PREFIX


async def get_server_job_stats():
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


async def _print(num):
    print(num)
