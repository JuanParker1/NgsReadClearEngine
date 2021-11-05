import subprocess
import time
import os
from contextlib import suppress

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
async def main():
    function_to_call = {sc.LONG_RUNNING_JOBS_NAME: print("long running"), sc.NEW_RUNNING_JOBS_NAME: p_running,
                        sc.QUEUE_JOBS_NAME:p_Q, sc.FINISHED_JOBS_NAME:p_f}
    listener = JobListener.PbsListener(function_to_call)
    asyncio.ensure_future(listener.run(10))
    for i in range(4):
        file_path = '/groups/pupko/alburquerque/NgsReadClearEngine/temp_sh.sh'
        with open(file_path, 'w+') as fp:
            fp.write(T)
        terminal_cmd = f'/opt/pbs/bin/qsub {str(file_path)}'
        subprocess.call(terminal_cmd, shell=True)
        os.remove(file_path)

    for i in range(20):
        file_path = '/groups/pupko/alburquerque/NgsReadClearEngine/temp_sh.sh'
        with open(file_path, 'w+') as fp:
            fp.write(T)
        terminal_cmd = f'/opt/pbs/bin/qsub {str(file_path)}'
        subprocess.call(terminal_cmd, shell=True)
        os.remove(file_path)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    # Let's also cancel all running tasks:
    # pending = asyncio.Task.all_tasks()
    # for task in pending:
    #     task.cancel()
    #     # Now we should await task to execute it's cancellation.
    #     # Cancelled task raises asyncio.CancelledError that we can suppress:
    #     with suppress(asyncio.CancelledError):
    #         loop.run_until_complete(task)