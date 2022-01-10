import boto3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
# from sklearn.externals import joblib
import joblib

import pandas as pd
from time import time
import re
import io
import json

# XRay instrumentation: https://docs.aws.amazon.com/lambda/latest/dg/python-tracing.html
from aws_xray_sdk.core import patch_all
patch_all()

s3_client = boto3.client('s3')

cleanup_re = re.compile('[^a-z]+')
tmp = '/tmp/'


def cleanup(sentence):
    sentence = sentence.lower()
    sentence = cleanup_re.sub(' ', sentence).strip()
    return sentence


def lambda_handler(event, context):
    event_body = json.loads(event['body'])
    dataset_bucket = event_body['dataset_bucket']
    dataset_object_key = event_body['dataset_object_key']
    model_bucket = event_body['model_bucket']
    model_object_key = event_body['model_object_key']  # example : lr_model.pk

    obj = s3_client.get_object(Bucket=dataset_bucket, Key=dataset_object_key)
    df = pd.read_csv(io.BytesIO(obj['Body'].read()))

    start = time()
    df['train'] = df['Text'].apply(cleanup)

    tfidf_vector = TfidfVectorizer(min_df=100).fit(df['train'])

    train = tfidf_vector.transform(df['train'])

    model = LogisticRegression()
    model.fit(train, df['Score'])
    latency = time() - start

    model_file_path = tmp + model_object_key
    joblib.dump(model, model_file_path)

    s3_client.upload_file(model_file_path, model_bucket, model_object_key)
    body = {
        'latency': latency
    }
    response = {
        'statusCode': 200,
        'body': json.dumps(body)
    }
    return response
