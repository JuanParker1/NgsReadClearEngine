import subprocess
import time
import os
from contextlib import suppress
from apscheduler.schedulers.background import BackgroundScheduler
import SharedConsts as sc
import JobListener
import asyncio
def p_running(a):
    print(f'new running {a}')
def p_error(a):
    print(f'error {a}')

def p_Q(a):
    print(f'Q {a}')

def p_f(a):
    print(f'finished {a}')


T = '''
#!/bin/bash

#PBS -S /bin/bash
#PBS -r y
#PBS -q itaym
#PBS -l ncpus=1
#PBS -v PBS_O_SHELL=bash,PBS_ENVIRONMENT=PBS_BATCH
#PBS -N KR_Test
#PBS -e /groups/pupko/alburquerque/NgsReadClearEngine/Temp/
#PBS -o /groups/pupko/alburquerque/NgsReadClearEngine/Temp/

source /groups/pupko/alburquerque/miniconda3/etc/profile.d/conda.sh
cd /groups/pupko/alburquerque/NgsReadClearEngine/
PYTHONPATH=$(pwd)

python "/groups/pupko/alburquerque/NgsReadClearEngine/to_run.py"

'''




if __name__ == '__main__':
    function_to_call = {sc.LONG_RUNNING_JOBS_NAME: print("long running"), sc.NEW_RUNNING_JOBS_NAME: p_running,
                        sc.QUEUE_JOBS_NAME:p_Q, sc.FINISHED_JOBS_NAME:p_f}
    listener = JobListener.PbsListener(function_to_call)
    scheduler = BackgroundScheduler()
    scheduler.add_job(listener.run, 'interval', seconds=30)
    scheduler.start()

    while True:
        for i in range(4):
            file_path = '/groups/pupko/alburquerque/NgsReadClearEngine/temp_sh.sh'
            with open(file_path, 'w+') as fp:
                fp.write(T)
            terminal_cmd = f'/opt/pbs/bin/qsub {str(file_path)}'
            subprocess.call(terminal_cmd, shell=True)
            os.remove(file_path)
        time.sleep(20)