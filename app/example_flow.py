import prefect
from prefect import task, Flow
import datetime
import random
from time import sleep
from prefect.run_configs import LocalRun
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
          executor=LocalDaskExecutor(),
          run_config=LocalRun()) as flow:
  incs = inc.map(x=range(3))
  decs = dec.map(x=range(3))
  adds = add.map(incs, decs)
  total = list_sum(adds)

print(flow.serialized_hash())
flow.register(project_name = 'event-driven-data-processing') #, idempotency_key=flow.serialized_hash())