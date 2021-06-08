import os
import boto3
import prefect
import pandas as pd
from prefect import task, Flow, Parameter
from prefect.run_configs import LocalRun
from prefect.executors import LocalDaskExecutor


@task
def extract(bucket, src_filename):
    s3_client = boto3.client('s3')
    s3_client.download_file(bucket, src_filename, src_filename)
    df = pd.read_csv(src_filename)
    return df


@task
def transform(df, src_filename):
    df_out = df.describe()
    dest_filename = src_filename.split('.')[0]+'_processed.csv'
    df_out.to_csv(dest_filename, index=False)
    return dest_filename


@task
def load(dest_filename, bucket, src_filename):
    s3_client = boto3.client('s3')
    s3_client.upload_file(Filename=dest_filename,
                          Bucket=bucket, Key=dest_filename)


@task
def cleanup(dest_filename, src_filename):
    os.remove(src_filename)
    os.remove(dest_filename)


with Flow('processing-etl',
          executor=LocalDaskExecutor(),
          run_config=LocalRun()) as flow:
    # parameters passed in via API call -- set with defaults here
    src_bucket = Parameter('src_bucket', default='eddp-src')
    src_filename = Parameter('src_filename', default='df_src.csv')
    extract_result = extract(src_bucket, src_filename)
    transform_result = transform(extract_result, src_filename)
    load_result = load(transform_result, src_bucket, src_filename)

    cleanup_result = cleanup(transform_result, src_filename)
    cleanup_result.set_upstream(load_result)

flow.run()