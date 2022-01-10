import logging
import json
import requests
import random

BENCHMARK_CONFIG = """
image_processing:
  description: Facial recognition workflow.
  provider: aws
  region: us-east-1
  root: ..
"""

IMAGE_KEYS = ["1_happy_face.jpg", "4_no_face.jpg"]
USER_NAME = "user_a"


def prepare(spec):
    # The deploy_id is used to generate globally unique S3 bucket names
    spec['deploy_id'] = spec['deploy_id'] or random.randint(1000, 9999)
    log = spec.run(f"./setup.sh {spec['region']} {spec['deploy_id']}", image='serverless_cli')
    indexes = [i for i, c in enumerate(log) if c == '\n']
    spec['endpoint_api_url'] = log[indexes[-4]+1 : indexes[-3]]
    spec['endpoint_state_machine_arn'] = log[indexes[-3]+1 : indexes[-2]]
    spec['endpoint_bucket_name'] = log[indexes[-2]+1 : indexes[-1]]
    logging.info(f"service endpoint_api_url={spec['endpoint_api_url']}")
    logging.info(f"service endpoint_state_machine_arn={spec['endpoint_state_machine_arn']}")
    logging.info(f"service endpoint_bucket_name={spec['endpoint_bucket_name']}")


def invoke(spec):
    face_img = IMAGE_KEYS[0]
    non_face_img = IMAGE_KEYS[1]
    # Native Python-based invocation
    # logging.info(send_request(spec['endpoint_api_url'], get_body(spec, face_img)))
    # logging.info(send_request(spec['endpoint_api_url'], get_body(spec, non_face_img)))

    # k6-based invocation
    envs = {
        'URL': spec['endpoint_api_url'],
        'STATE_MACHINE_ARN': spec['endpoint_state_machine_arn'],
        'USER_ID': USER_NAME,
        'S3_BUCKET': spec['endpoint_bucket_name'],
        'S3_KEY': face_img,
        'S3_KEY2': non_face_img,
    }
    spec.run_k6(envs)


def cleanup(spec):
    spec.run(f"./remove.sh {spec['region']} {spec['deploy_id']}", image='serverless_cli')


def send_request(url, body):
    resp = requests.post(url=url, data=body)
    if resp.status_code == 200:
        logging.info(f"response={resp.json()}")
        return resp.json()
    else:
        return "Failed send_request() with error code " + str(resp.status_code)


def get_body(spec, s3_key):
    """Returns a body string to invoke the application for a given s3_key.
    Notice the double JSON encoding of the input parameter, which makes it
    hard to serialize and deserialize properly.
    Example:
    {"input": "{\"userId\": \"user_a\", \"s3Bucket\": \"wildrydes-riderphotos3bucket-neeopydk0iuu\", \"s3Key\": \"1_happy_face.jpg\"}", "stateMachineArn": "arn:aws:states:us-east-1:123456789012:stateMachine:RiderPhotoProcessing-T53Fq3g7OeOZ"}
    """
    return json.dumps({
        "input": json.dumps({
            "userId": USER_NAME,
            "s3Bucket": spec['endpoint_bucket_name'],
            "s3Key": s3_key,
        }),
        "stateMachineArn": spec['endpoint_state_machine_arn']
    })
