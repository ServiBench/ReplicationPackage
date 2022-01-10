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
import requests
import json

TIMEZONE='Europe/Zurich'

def setup():
    lambda_client = boto3.client('lambda')
    aws_uid = os.environ['AWS_ACCOUNT_UID']
    function_name = 'fab_api_trigger'
    api_client = boto3.client('apigateway')
    api_name = 'api_trigger'
    stage_name = 'staging'
    api_path = 'test'

    build_function()
    create_function(lambda_client, aws_uid, 'function.zip', function_name)
    api_id, endpoint_id = create_api_gateway(api_client, api_name, api_path)
    endpoint = bind_gw_to_lambda(api_client, api_id, endpoint_id, function_name, stage_name, api_path)
    if endpoint is None:
        logging.info('Unable to bind gateway to lambda function: ' + function_name + '. Exiting...')
        exit(1)
    logging.info('API Gateway bound to lambda function: ' + endpoint)

    # TODO: Standardize config passing/persistency between benchmark phases
    config = { 'endpoint': endpoint, 'api_id': api_id }
    fh = open('config.json', 'w')
    json.dump(config, fh)

def execute():
    # endpoint from setup()
    fh = open('config.json', 'r')
    config = json.load(fh)
    endpoint = config['endpoint']
    num_iterations = 10

    for _ in range(num_iterations):
        query_endpoint(endpoint)

def cleanup():
    # api_id from setup()
    fh = open('config.json', 'r')
    config = json.load(fh)
    api_id = config['api_id']

    lambda_client = boto3.client('lambda')
    aws_uid = os.environ['AWS_ACCOUNT_UID']
    function_name = 'fab_api_trigger'
    api_client = boto3.client('apigateway')
    api_name = 'api_trigger'
    stage_name = 'staging'
    api_path = 'test'

    remove_gw_api_bindings(api_client, api_id, stage_name, function_name)
    remove_api_gateway(api_client, api_name)
    remove_lambda_Function(lambda_client, aws_uid, function_name)

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

def create_api_gateway(api_client, api_name, child_resource_name):
    # taken from
    # https://docs.aws.amazon.com/code-samples/latest/catalog/python-lambda-lambda_with_api_gateway.py.html

    try:
        result = api_client.create_rest_api(name=api_name)
    except ClientError as e:
        logging.error(e)
        return None
    api_id = result['id']
    logging.info(f'Created REST API: {result["name"]}, ID: {api_id}')

    try:
        result = api_client.get_resources(restApiId=api_id)
    except ClientError as e:
        logging.error(e)
        return None
    root_id = None
    for item in result['items']:
        if item['path'] == '/':
            root_id = item['id']
    if root_id is None:
        logging.error('Could not retrieve the ID of the API\'s root resource.')
        return None

    try:
        result = api_client.create_resource(restApiId=api_id,
                                            parentId=root_id,
                                            pathPart=child_resource_name)
    except ClientError as e:
        logging.error(e)
        return None
    endpoint_id = result['id']

    try:
        api_client.put_method(restApiId=api_id,
                              resourceId=endpoint_id,
                              httpMethod='ANY',
                              authorizationType='NONE')
    except ClientError as e:
        logging.error(e)
        return None

    content_type = {'application/json': 'Empty'}
    try:
        api_client.put_method_response(restApiId=api_id,
                                       resourceId=endpoint_id,
                                       httpMethod='ANY',
                                       statusCode='200',
                                       responseModels=content_type)
    except ClientError as e:
        logging.error(e)
        return None

    return api_id, endpoint_id

def bind_gw_to_lambda(api_client, api_id, endpoint_id, function_name,
                      stage_name, child_resource_name):
    # Set the Lambda function as the destination for the ANY method
    # Extract the Lambda region and AWS account ID from the Lambda ARN
    # ARN format="arn:aws:lambda:REGION:ACCOUNT_ID:function:FUNCTION_NAME"
    lambda_arn = get_lambda_arn(function_name)
    if lambda_arn is None:
        return None
    sections = lambda_arn.split(':')
    region = sections[3]
    account_id = sections[4]
    # Construct the Lambda function's URI
    lambda_uri = f'arn:aws:apigateway:{region}:lambda:path/2015-03-31/' \
        f'functions/{lambda_arn}/invocations'
    try:
        api_client.put_integration(restApiId=api_id,
                                   resourceId=endpoint_id,
                                   httpMethod='ANY',
                                   type='AWS',
                                   integrationHttpMethod='POST',
                                   uri=lambda_uri)
    except ClientError as e:
        logging.error(e)
        return None

    # Set the content-type of the Lambda function to JSON
    content_type = {'application/json': ''}
    try:
        api_client.put_integration_response(restApiId=api_id,
                                            resourceId=endpoint_id,
                                            httpMethod='ANY',
                                            statusCode='200',
                                            responseTemplates=content_type)
    except ClientError as e:
        logging.error(e)
        return None

    # Deploy the API
    try:
        deployment = api_client.create_deployment(restApiId=api_id,
                                                  stageName=stage_name)
        logging.debug('Deployment created - deployment = ', deployment)
    except ClientError as e:
        logging.error(e)
        return None

    # Grant invoke permissions on the Lambda function so it can be called by
    # API Gateway.
    # Note: To retrieve the Lambda function's permissions, call
    # Lambda.Client.get_policy()
    source_arn = f'arn:aws:execute-api:{region}:{account_id}:{api_id}/*/*/{child_resource_name}'
    lambda_client = boto3.client('lambda')
    try:
        lambda_client.add_permission(FunctionName=function_name,
                                     StatementId=f'{function_name}-invoke',
                                     Action='lambda:InvokeFunction',
                                     Principal='apigateway.amazonaws.com',
                                     SourceArn=source_arn)
    except ClientError as e:
        logging.error(e)
        return None

    # Construct the API URL
    api_url = f'https://{api_id}.execute-api.{region}.amazonaws.com/{stage_name}/{child_resource_name}'
    logging.info(f'API base URL: {api_url}')
    return api_url

def get_lambda_arn(lambda_name):
    """Retrieve the ARN of a Lambda function

    :param lambda_name: Name of Lambda function
    :return: String ARN of Lambda function. If error, returns None.
    """

    # Retrieve information about the Lambda function
    lambda_client = boto3.client('lambda')
    try:
        response = lambda_client.get_function(FunctionName=lambda_name)
    except ClientError as e:
        logging.error(e)
        return None
    return response['Configuration']['FunctionArn']

def get_current_time(timezone):
    now = datetime.datetime.now()
    localtz = pytz.timezone(timezone)
    now_tz = localtz.localize(now)
    return now_tz

def query_endpoint(endpoint):
    start_time  = datetime.datetime.now()
    response = requests.get(endpoint)
    end_time = datetime.datetime.now()
    delta = end_time - start_time
    logging.info(f'Start {start_time}, End {end_time}, delta {(delta.microseconds/1000)} ms')

def remove_gw_api_bindings(api_client, api_id, stage_name, function_name):
    try:
        api_client.delete_stage(restApiId=api_id, stageName=stage_name)
    except ClientError as e:
        logging.error(e)
        return None

    # remove the deployment
    try:
        deployments = api_client.get_deployments(restApiId=api_id)
    except ClientError as e:
        logging.error(e)
        return None

    if len(deployments['items']) > 1:
        logging.info('Number of deployments > 1....exiting...')

    deployment_id = deployments['items'][0]['id']

    try:
        api_client.delete_deployment(restApiId=api_id,
                                     deploymentId=deployment_id)
    except ClientError as e:
        logging.error(e)
        return None

def remove_api_gateway(api_client, api_name):
    try:
        result = api_client.get_rest_apis()
    except ClientError as e:
        logging.error(e)
        return None
    for api in result['items']:
        if api['name'] == api_name:
            logging.debug(f'api = {api}')
            api_id = api['id']
    if api_id is None:
        logging.warning('Error finding REST API')

    try:
        result = api_client.delete_rest_api(restApiId=api_id)
        logging.info(f'Deleted REST API: {api_name}, ID: {api_id}')
    except ClientError as e:
        logging.error(e)
        return None

def remove_lambda_Function(l, aws_uid, function_name):
    try:
        l.delete_function(FunctionName=function_name)
        logging.debug('Function deleted: ' + function_name)
    except ClientError as e:
        logging.warning('Error deleting function: ' + function_name, e)


def main():
    logging.basicConfig(stream=sys.stdout,level=logging.INFO)
    setup()
    execute()
    cleanup()

if __name__ == "__main__":
    main()
