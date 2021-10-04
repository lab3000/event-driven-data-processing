#!/usr/bin/env python

from json import loads
from prefect import task, Flow
from prefect.tasks.shell import ShellTask

shell_task = ShellTask(return_all=True,log_stderr=True,stream_output='DEBUG')

@task(log_stdout=True)
def get_login_str(response):
    api_key = loads(response[0])["prefect-api-key1"]
    return 'prefect auth login -t '+api_key

@task(log_stdout=True)
def create_agent_install_str(token):
    return 'prefect agent install kubernetes -t '+token[0]

@task(log_stdout=True)
def print_rslt(r):
    print(r)

with Flow('connect_prefect1') as f:
    cli_str = 'aws secretsmanager get-secret-value --secret-id  dev/event-driven/prefect1'
    cli_str = cli_str+' --query SecretString --output text --region us-west-2'
    secr_mng_response = shell_task(command=cli_str, task_args=dict(name='shell: aws secretsmanager call',log_stdout=True))

    login_str = get_login_str(secr_mng_response)
    login_response = shell_task(command=login_str, task_args=dict(name='shell: prefect auth login',log_stdout=True))
    print_rslt(login_response)

    token_str = 'prefect auth create-token -n my-runner-token -s RUNNER'
    runner_token = shell_task(command=token_str, task_args=dict(name='shell: prefect auth create-token',log_stdout=True))
    runner_token.set_upstream(login_response)

    set_backend = shell_task(command='prefect backend cloud', task_args=dict(name='shell: prefect backend cloud',log_stdout=True))
    set_backend.set_upstream(runner_token)

    # could eventually replace this with executing a python file that loops through 
    # to register all flows to be registered (use a flow to loop over shell_task tasks and use flow.run())
    # use string manipulations to insert the project name by passing a project_name parameter to a task
    register_flow = shell_task(command='python ./example_flow.py', task_args=dict(name='shell: register flow',log_stdout=True)) #'prefect register --path ./example_flow.py --project event-driven-data-processing --force', task_args=dict(name='shell: register flow'))
    register_flow.set_upstream(set_backend)

    start_str = create_agent_install_str(runner_token)
    start_agent = shell_task(command=start_str, task_args=dict(name='shell: prefect agent install',log_stdout=True)) 
    start_agent.set_upstream(register_flow)

f.run()
