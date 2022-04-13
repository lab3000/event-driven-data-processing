import stat
import boto3
from json import loads
from time import sleep
from prefect import task, Flow, Parameter
from prefect.tasks.shell import ShellTask
from prefect.agent.local import LocalAgent

'''
if flows are meant to be run on kubernetes, 
each flow should have it's corresponding ecr repo created automatically
TODO: set up such automation depending on the flow config
'''
@task(log_stdout=True)
def get_flows():
    # add any flows you'd like to register
    # TODO: automatically pull all flows from a /flows path
    pre = 'poetry run python3 '
    flows = ['./example_flow.py','./shutdown_eks.py']
    return [pre+f for f in flows]

register_flows = ShellTask(return_all=True, log_stderr=True, stream_output='DEBUG',
                           name='register flows', log_stdout=True)

shell_task = ShellTask(return_all=True, log_stderr=True, stream_output='DEBUG')

@task(log_stdout=True)
def wait_for_eks(config_path):
    check = True
    while check == True:
        with open(config_path) as f:
            config_ = f.read()
        if 'fargate' in config_:
            check = 'fargate successfully up'
        else:
            print('sleeping before next check')
            sleep(10)
            continue
    return check


@task(log_stdout=True)
def get_login_str(response):
    api_key = loads(response[0])["prefect-api-key1"]
    return 'prefect auth login --key '+api_key


@task(log_stdout=True)
def create_agent_install_str(token):
    str_ = 'prefect agent kubernetes install -t ' + \
        token[1]+' --label eddp-1-prefect-k8-agent-label --rbac >> k8s_agent.yml'
    print(str_)
    return str_


@task(log_stdout=True)
def print_rslt(r):
    print(r)

@task(log_stdout=True)
def get_ecr_path():
    ssm = boto3.client('ssm')
    param_response = ssm.get_parameter(Name='ecr_path')
    ecr_path = param_response['Parameter']['Value']
    return ecr_path

@task(log_stdout=True)
def get_ecr_login(ecr_path):
    part1 = 'sudo aws ecr get-login-password --region us-west-1 |'
    part2 = ' docker login --username AWS --password-stdin '
    repo = ecr_path+'/getting-started-example'
    return part1+part2+repo

'''local agent started in EC2 UserData startup'''
@task(log_stdout=True)
def start_local_agent():
    LocalAgent(labels=['eddp_ec2_local']).start()

with Flow('connect_prefect1') as f:

    # wait for eks_cluster to spin up
    mod_permission = shell_task(command='sudo chmod 666 ./.kube/config', task_args=dict(
        name='shell: mod permission on kube config', log_stdout=True))
    eks_up = wait_for_eks('./.kube/config')
    eks_up.set_upstream(mod_permission)

    cli_str = 'aws secretsmanager get-secret-value --secret-id  dev/event-driven/prefect1'
    cli_str = cli_str+' --query SecretString --output text --region us-west-2'
    secr_mng_response = shell_task(command=cli_str, task_args=dict(
        name='shell: aws secretsmanager call', log_stdout=True))
    secr_mng_response.set_upstream(eks_up)

    login_str = get_login_str(secr_mng_response)
    login_response = shell_task(command=login_str, task_args=dict(
        name='shell: prefect auth login', log_stdout=True))
    print_rslt(login_response)

    token_str = 'prefect auth create-token -n my-runner-token -s RUNNER'
    runner_token = shell_task(command=token_str, task_args=dict(
        name='shell: prefect auth create-token', log_stdout=True))
    runner_token.set_upstream(login_response)

    set_backend = shell_task(command='prefect backend cloud', task_args=dict(
        name='shell: prefect backend cloud', log_stdout=True))
    set_backend.set_upstream(runner_token)

    # Deploy prefect Kubernetes agent on the EKS cluster
    agent_install_str = create_agent_install_str(runner_token)
    agent_template = shell_task(command=agent_install_str, task_args=dict(
        name='shell: create agent install template', log_stdout=True))
    agent_template.set_upstream(set_backend)

    kubeconfig_updated = shell_task('sudo aws eks update-kubeconfig --name fargate-eks --region us-west-1',
                                    task_args=dict(name='updating kubeconfig', log_stdout=True))
    kubeconfig_updated.set_upstream(agent_template)

    k8_agent_installed = shell_task(command='sudo kubectl apply -f k8s_agent.yml',
                                    task_args=dict(name='shell: start k8s prefect agent', log_stdout=True))
    k8_agent_installed.set_upstream(kubeconfig_updated)

    # Install Flows
    ecr_path = get_ecr_path()
    ecr_path.set_upstream(k8_agent_installed)
    ecr_login_str = get_ecr_login()
    ecr_login_str.set_upstream(ecr_path)

    ecr_logged_in = shell_task(command=ecr_login_str, task_args=dict(
        name='shell: log into ecr', log_stdout=True))

    flows_to_register = get_flows()
    registered_flows = register_flows.map(flows_to_register)
    registered_flows.set_upstream(ecr_logged_in)

    # Start local agent
    start_local_agent()
    start_local_agent.set_upstream(registered_flows)


f.run()
