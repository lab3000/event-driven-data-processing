#!/usr/bin/env python

import sys
from json import loads
from prefect import task, Flow
from prefect.tasks.shell import ShellTask

# prefect_api_key = loads(sys.stdin.read())
# print('type(prefect_api_key) = ', type(prefect_api_key))
# print('prefect_api_key = ', prefect_api_key)

# print(prefect_api_key['prefect-api-key1'])

aws_get_secret = ShellTask()
prefect_login = ShellTask()
create_token = ShellTask()
export_token = ShellTask()
set_backend = ShellTask()

@task
def get_login_str(response):
    api_key = loads(response)['prefect-api-key1']
    return 'prefect auth login -t '+api_key

@task
def create_export_str(token):
    return 'export PREFECT__CLOUD__AGENT__AUTH_TOKEN='+token

@task
def print_rslt(r):
    print(r)

with Flow('connect_prefect') as f:
    cli_str = 'aws secretsmanager get-secret-value --secret-id'
    cli_str = cli_str+' dev/event-driven/prefect1 --query SecretString --output text'
    secr_mng_response = aws_get_secret(command=cli_str)

    login_str = get_login_str(secr_mng_response)
    login_response = prefect_login(command=login_str)
    print_rslt(login_response)

    token_str = 'prefect auth create-token -n my-runner-token -s RUNNER'
    runner_token = create_token(command=token_str)
    export_str = create_export_str(runner_token)
    export_token(command=export_token)

    set_backend(command='prefect backend cloud')

f.set_dependencies(task=create_token,upstream_tasks=[prefect_login])
f.set_dependencies(task=set_backend,upstream_tasks=[export_token])
f.run()