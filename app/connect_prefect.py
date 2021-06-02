#!/usr/bin/env python

import sys
from json import loads
from prefect import task, Flow
from prefect.tasks.shell import ShellTask

shell_task = ShellTask(return_all=True,log_stderr=True,stream_output='DEBUG')

@task
def get_login_str(response):
    api_key = loads(response[0])["prefect-api-key1"]
    return 'prefect auth login -t '+api_key

@task
def create_start_str(token):
    print('token[0] = ',token[0])
    return 'prefect agent start -t '+token[0]

@task
def print_rslt(r):
    print(r)

with Flow('connect_prefect1') as f:
    cli_str = 'aws secretsmanager get-secret-value --secret-id  dev/event-driven/prefect1'
    cli_str = cli_str+' --query SecretString --output text --region us-west-2'
    secr_mng_response = shell_task(command=cli_str)

    login_str = get_login_str(secr_mng_response)
    login_response = shell_task(command=login_str)
    print_rslt(login_response)

    token_str = 'prefect auth create-token -n my-runner-token -s RUNNER'
    runner_token = shell_task(command=token_str)
    runner_token.set_upstream(login_response)

    set_backend = shell_task(command='prefect backend cloud')
    set_backend.set_upstream(runner_token)

    register_flow = shell_task(command='python ./example_flow.py')
    register_flow.set_upstream(set_backend)

    start_str = create_start_str(runner_token)
    start_agent = shell_task(command=start_str) 
    start_agent.set_upstream(register_flow)

f.run()
