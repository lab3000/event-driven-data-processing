from json import loads
from prefect import task, Flow
from prefect.tasks.shell import ShellTask
import pandas as pd
# from prefect.run_configs import LocalRun
# from prefect.executors import LocalDaskExecutor

df = pd.DataFrame({'A':[1,2,3],'B':[4,5,6]})

df.to_pickle('ec2_init_df.p')

shell_task = ShellTask(return_all=True,log_stderr=True,stream_output='DEBUG')

@task(log_stdout=True)
def make_curl_str(nr_api_key, nr_account_id):
    api_key = loads(nr_api_key[0])["nr_api_key"]
    account_id = loads(nr_account_id[0])["nr_account_id"]
    curl_str = 'curl -Ls https://download.newrelic.com/install/newrelic-cli/scripts/install.sh'
    curl_str = curl_str+' | bash && sudo  NEW_RELIC_API_KEY='+api_key
    curl_str = curl_str+' NEW_RELIC_ACCOUNT_ID='+account_id+' /usr/local/bin/newrelic install -n logs-integration -y'
    return curl_str

@task(log_stdout=True)
def print_rslt(r):
    print(r)

# dash executor allows parallel execution of non-dependent tasks
with Flow('connect_prefect') as f:
    # ,
    #       executor=LocalDaskExecutor(),
    #       run_config=LocalRun()) as f:

    cli_str0 = 'export AWS_DEFAULT_REGION=us-west-1'
    set_region = shell_task(command=cli_str0, task_args=dict(name='set AWS region',log_stdout=True))

    # cli_str1 = 'aws secretsmanager get-secret-value --secret-id  dev/eddp/nr_account_id'
    # cli_str1 = cli_str1+' --query SecretString --output text --region us-west-1'
    # nr_account_id = shell_task(command=cli_str1, task_args=dict(name='get nr_api_key from secretsmanager',log_stdout=True))
    # nr_account_id.set_upstream(install_eksctl)

    # cli_str2 = 'aws secretsmanager get-secret-value --secret-id  dev/eddp/nr_api_key'
    # cli_str2 = cli_str2+' --query SecretString --output text --region us-west-1'
    # nr_api_key = shell_task(command=cli_str2, task_args=dict(name='get nr_account_id from secretsmanager',log_stdout=True))
    # nr_api_key.set_upstream(nr_account_id)

    # nr_curl_str = make_curl_str(nr_api_key, nr_account_id)
    # nr_install = shell_task(command=nr_curl_str, task_args=dict(name='installing New Relic',log_stdout=True))

    cli_str = 'sudo curl --silent --location '
    cli_str = cli_str+'"https://github.com/weaveworks/eksctl/releases/latest/download/eksctl_$(uname -s)_amd64.tar.gz" |'
    cli_str = cli_str+" tar xz -C /tmp && sudo mv ../../tmp/eksctl ../../usr/local/bin" 
    install_eksctl = shell_task(command=cli_str, task_args=dict(name='install eksctl',log_stdout=True))
    # install_eksctl.set_upstream(nr_install)

    # create eks fargate cluster
    # cli_str = 'eksctl create cluster --name fargate-eks --region us-west-1 --fargate'
    # eks_cluster = shell_task(command=cli_str, task_args=dict(name='create eks cluster',log_stdout=True))
    # eks_cluster.set_upstream(install_eksctl)
    # created eks cluster will be a continually running process so nothing follows it directly in the flow
    # but wait_for_eks task, in the connect_prefect flow, will discover when that flow is ready to kick-off
   
f.run()


