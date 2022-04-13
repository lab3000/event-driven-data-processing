import prefect
from prefect import task, Flow
from prefect.storage import Docker
# from prefect.environments import DaskKubernetesEnvironment
import datetime
import random
from time import sleep
from prefect.run_configs import LocalRun, KubernetesRun
from prefect.executors import LocalDaskExecutor

@task
def inc(x):
  sleep(random.random() / 10)
  return x + 1

@task
def dec(x):
  sleep(random.random() / 10)
  return x-1

@task
def add(x, y):
  sleep(random.random() / 10)
  return x + y
  
@task(name='sum')
def list_sum(arr):
  logger = prefect.context.get("logger")
  logger.info(f"total sum : {sum(arr)}")  
  return sum(arr)

with Flow('getting-started-example',
          storage=Docker(registry_url="091442718550.dkr.ecr.us-west-1.amazonaws.com",
                         python_dependencies=["pandas==1.1.0"],
                         image_tag='latest'),
          run_config=KubernetesRun(labels=["eddp-1-prefect-k8-agent-label"])) as flow:
  incs = inc.map(x=range(3))
  decs = dec.map(x=range(3))
  adds = add.map(incs, decs)
  total = list_sum(adds)

print(flow.serialized_hash())
if __name__=='__main__':  
  # flow.environment = DaskKubernetesEnvironment(min_workers=3, max_workers=5)
  flow.register(project_name = 'event-driven-data-processing') #, idempotency_key=flow.serialized_hash())