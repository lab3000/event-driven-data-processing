from prefect import task, Flow, case
from prefect.tasks.shell import ShellTask
from prefect.run_configs import LocalRun
from datetime import timedelta

'''
This script automates this EKS shutdown guide:
https://docs.aws.amazon.com/eks/latest/userguide/delete-cluster.html
'''

shell_task = ShellTask(return_all=True, log_stderr=True, stream_output='DEBUG')


@task(log_stdout=True)
def get_kube_services_to_delete(response):
    # api_key = loads(response[0])["prefect-api-key1"]
    # return 'prefect auth login --key '+api_key
    print(type(response))
    services_to_delete = []
    for i, r in enumerate(response):
        if i > 0:
            line_cols = r.split(' ')
            if '<none>' in line_cols[4]:  # col 4 is the EXTERNAL-IP value
                service_nm = line_cols[0].strip(' ')
                services_to_delete.append(service_nm)
    print('services_to_delete = ', services_to_delete)
    return services_to_delete


@task(log_stdout=True)
def check_service_list(services):
    if len(services) > 0:
        return True
    else:
        return False


@task(log_stdout=True)
def get_service_del_str(service):
    return 'sudo kubectl delete svc '+service


@task(log_stdout=True)
def get_node_grps_to_del(response):
    print('printing list_node_grps_response')
    print(type(response))
    print(response)
    node_groups = response[1].split('[')[1].split(']')[0].split(',')
    print('printing node group info')
    print(type(node_groups))
    print(node_groups)


@task(log_stdout=True)
def check_node_groups(node_grps):
    if node_grps == None:
        print('delete node groups = False')
        return False
    else:
        print('delete node groups = True')
        return True


@task(log_stdout=True)
def get_node_del_str(node_grp):
    del_str = 'aws eks delete-nodegroup --nodegroup-name ' + \
        node_grp+' --cluster-name fargate-eks --region us-west-1'
    return del_str


@task(log_stdout=True)
def get_profiles(profiles_response):
    print('printing profiles response!')
    print(type(profiles_response))
    print(profiles_response)
    prof_prep = profiles_response[2:-1]
    profiles = []
    for prof in prof_prep:
        if '"' in prof:
            profiles.append(prof.split('"')[1])
    return profiles


@task(log_stdout=True)
def make_profiles_del_str(profile_str):
    del_str = 'aws eks delete-fargate-profile --fargate-profile-name ' + \
        profile_str+' --cluster-name fargate-eks --region us-west-1'
    print(del_str)
    return del_str


@task(log_stdout=True)
def get_eks_stack(stack_nms):
    print(stack_nms)
    eks_stack_nm = [s for s in stack_nms if 'eks' in s][0].split('"')[1]
    print(eks_stack_nm)
    return eks_stack_nm


@task(log_stdout=True)
def get_eks_stack_del_str(eks_stack_nm):
    stack_del_str = 'aws cloudformation delete-stack --stack-name ' + \
        eks_stack_nm+' --region us-west-1'
    print(stack_del_str)
    return stack_del_str


delete_nodes = ShellTask(return_all=True, log_stderr=True,
                         stream_output='DEBUG', name='node grp deletion', log_stdout=True)
delete_services = ShellTask(return_all=True, log_stderr=True,
                            stream_output='DEBUG', name='service deletion', log_stdout=True)
delete_profiles = ShellTask(return_all=True, log_stderr=True,
                            stream_output='DEBUG', name='profile deletion', log_stdout=True)

# this flow automates this shutdown process https://docs.aws.amazon.com/eks/latest/userguide/delete-cluster.html
with Flow('shutdown_eks',run_config=LocalRun(labels=['eddp_ec2_local'])) as f:

    svc_response = shell_task(command='sudo kubectl get svc --all-namespaces',
                              task_args=dict(name='shell: get svc namespaces', log_stdout=True))
    service_del_list = get_kube_services_to_delete(
        svc_response)  # returns a list
    delete_services = check_service_list(
        service_del_list)  # returns True if len(list)>0

    with case(delete_services, True):
        service_del_strs = get_service_del_str.map(service_del_list)
        dels_svc = delete_services.map(service_del_strs)

    # later can make <my-cluster> (fargate-eks) a parameter
    list_node_grps_response = shell_task(
        command='aws eks list-nodegroups --cluster-name fargate-eks --region us-west-1', task_args=dict(name='cli get nodegroups', log_stdout=True))
    node_groups = get_node_grps_to_del(list_node_grps_response)
    delete_node_groups = check_node_groups(node_groups)

    with case(delete_node_groups, True):
        node_del_strs = get_node_del_str.map(node_groups)
        dels_node_grps = delete_nodes.map(node_del_strs)

    profiles_response = shell_task(command='aws eks list-fargate-profiles --cluster-name fargate-eks --region us-west-1',
                                   task_args=dict(name='shell: get profiles', log_stdout=True))
    profiles = get_profiles(profiles_response)
    profiles_del_strs = make_profiles_del_str.map(profiles)
    dels_profiles = delete_profiles.map(profiles_del_strs)

    cld_frmn_stacks = shell_task(command='aws cloudformation list-stacks --query "StackSummaries[].StackName" --region us-west-1',
                                 task_args=dict(name='get stack names', log_stdout=True))
    eks_stack_nm = get_eks_stack(cld_frmn_stacks)

    del_eks_stack_str = get_eks_stack_del_str(eks_stack_nm)

    del_stack = shell_task(command=del_eks_stack_str, task_args=dict(
        name='delete eks cloudformation stack', log_stdout=True))

    # # later can make <my-cluster> (fargate-eks) a parameter
    del_cluster = shell_task(command='aws eks delete-cluster --name fargate-eks --region us-west-1',
                             task_args=dict(name='delete cluster', log_stdout=True, max_retries=20,
                                            retry_delay=timedelta(seconds=30)))
    del_cluster.set_upstream(del_stack)

if __name__=='__main__':  
  # flow.environment = DaskKubernetesEnvironment(min_workers=3, max_workers=5)
  f.register(project_name = 'event-driven-data-processing')
