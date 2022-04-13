import os
from time import sleep
from json import loads
from prefect import task, Flow
from prefect.tasks.shell import ShellTask

shell_task = ShellTask(return_all=True,log_stderr=True,stream_output='DEBUG')

@task(log_stdout=True)
# wait for k8 file with os.listdir
# this is created by the agent_template task in connect_prefect.py
def wait_for_agent_template():
    check=True
    while check==True:
        files_ = os.listdir()
        if 'k8s_agent.yml' in files_:
            check=False
    
    return 'sudo kubectl apply -f k8s_agent.yml'

with Flow('start_k8_agent') as f:

    apply_agent_str = wait_for_agent_template()

    start_agent = shell_task(command=apply_agent_str, task_args=dict(name='shell: start k8s prefect agent',log_stdout=True))

f.run()