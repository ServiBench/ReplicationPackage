import os
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
import logging
import datetime
from dateutil import parser
import pytz
import re
import sys

TIMEZONE='Europe/Zurich'

def setup():
    l = boto3.client('lambda')
    aws_uid = os.environ['AWS_ACCOUNT_UID']
    function_name = 'fab_direct_trigger'

    build_function()
    create_function(l, aws_uid, 'function.zip', function_name)

def execute():
    l = boto3.client('lambda')
    aws_uid = os.environ['AWS_ACCOUNT_UID']
    function_name = 'fab_direct_trigger'
    num_iterations = 10

    logging.info(f'Results for {num_iterations} synchronous function invocations:')
    for i in range(num_iterations):
        local_invocation_time = get_current_time(TIMEZONE)
        platform_invocation_time = invoke_function_sync(l, aws_uid, function_name, 'RequestResponse')
        time_delta = platform_invocation_time - local_invocation_time
        sample = { 'local_invocation_time': local_invocation_time, 'platform_invocation_time': platform_invocation_time, 'time_delta': time_delta }
        logging.info(f'Local Invocation Time: {local_invocation_time}, Platform Invocation Time: {platform_invocation_time}, Delta: {time_delta}')

def cleanup():
    l = boto3.client('lambda')
    aws_uid = os.environ['AWS_ACCOUNT_UID']
    function_name = 'fab_direct_trigger'

    remove_lambda_Function(l, aws_uid, function_name)

def build_function():
    # Build package must be called `main` by convention for AWS Lambda
    os.system('GOARCH=amd64 GOOS=linux go build -o main .')
    # AWS Lambda requires zip file
    os.system('zip function.zip main')
    # Clean up
    os.system('rm main')

def create_function(l, aws_uid, filename, function_name, dlq=None):
    role_string = 'arn:aws:iam::' + aws_uid + ':role/lambda_execution_role'
    zipfile = Path(filename).read_bytes()

    try:
        response = l.get_function(FunctionName=function_name)
        logging.info('Function already exists. Not updating: ' + function_name)
    except ClientError as e:
        if dlq is None:
            # create function
            l.create_function(FunctionName=function_name, Runtime='go1.x',
                    Handler='main', Code={'ZipFile': zipfile},
                    Role=role_string)
        else:
            # create function
            dlq_object = { 'TargetArn': dlq }
            l.create_function(FunctionName=function_name, Runtime='go1.x',
                    Handler='main', Code={'ZipFile': zipfile},
                    Role=role_string, DeadLetterQueue=dlq_object)

def get_current_time(timezone):
    now = datetime.datetime.now()
    localtz = pytz.timezone(timezone)
    now_tz = localtz.localize(now)
    return now_tz

def invoke_function_sync(l, uid, function_name, invocation_type):
    response = l.invoke(FunctionName=function_name, InvocationType=invocation_type,
            LogType='Tail', Payload='')
    payload = response['Payload']
    message = payload.read()
    message_utf = message.decode('utf-8')
    re_match = re.match("\"Current time = (.*) \+0000 (.*)", message_utf)
    # 2019-10-16 15:52:50.760602705 +0000 UTC
    # not considering timezone for now; also nanosecond parsing not supported by python

    invocation_time_str = re_match[1]
    invocation_time = datetime.datetime.strptime(invocation_time_str[:-3], "%Y-%m-%d %H:%M:%S.%f")
    invocation_time_tz = pytz.utc.localize(invocation_time)
    # logging.info('Invocation time = {}'.format(invocation_time))
    return invocation_time_tz

def remove_lambda_Function(l, aws_uid, function_name):
    try:
        l.delete_function(FunctionName=function_name)
        logging.debug('Function deleted: ' + function_name)
    except ClientError as e:
        logging.warn('Error deleting function: ' + function_name, e)


def main():
    logging.basicConfig(stream=sys.stdout,level=logging.INFO)
    setup()
    execute()
    cleanup()

if __name__ == "__main__":
    main()
