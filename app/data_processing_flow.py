import os
import boto3
import prefect
from prefect import task, Flow
from prefect.run_configs import LocalRun
from prefect.executors import LocalDaskExecutor


@task
def extract(bucket, src_filename):
    s3_client = boto3.client('s3')
    s3_client.download_file(bucket, src_filename)
    df = pd.read_csv(src_filename)
    return df, src_filename


@task
def transform(df, src_filename):
    df_out = df.describe()
    dest_filename = src_filename.split('.')[0]+'_processed.csv'
    df_out.to_csv(dest_filename, index=False)
    return dest_filename


@task
def load(bucket, src_filename, dest_filename):
    s3_client = boto3.client('s3')
    s3_client.upload_file(Filename=dest_filename,
                          Bucket=bucket, Key=dest_filename)


@task
def cleanup(src_filename, dest_filename):
    os.remove(src_filename)
    os.remove(dest_filename)


with Flow('processing-etl',
          executor=LocalDaskExecutor(),
          run_config=LocalRun()) as flow:
    # parameters passed in via API call -- set with defaults here
    extract_result = extract(param_bucket, param_src_flnm)
    transform_result = transform(extract_result)
    load_result = load(transform_result)
    cleanup_result = cleanup(load_result)