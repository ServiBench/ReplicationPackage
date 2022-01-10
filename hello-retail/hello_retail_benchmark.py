import base64
import logging
import random
import re

BENCHMARK_CONFIG = """
hello_retail:
  description: Event-driven Retail application with HTTP api.
  provider: aws
  region: us-east-1
  stage: dev
  team: specrg
  company: cloud
"""


# API calls, ew=event-writer, pr=product-receive, pc=product-catalog


# SB calls

def prepare(spec):
  # The deploy_id is used to generate globally unique S3 bucket names
  spec['deploy_id'] = spec['deploy_id'] or random.randint(1000, 9999)

  # Better ensure all dependencies are up to date than saving ~30s with conditional installation
  spec.run(f"./install.sh {spec['region']} {spec['stage']} {spec['company']} {spec['team']} {domain_name(spec)}", image='serverless_cli')

  log = spec.run(f"./deploy.sh {spec['region']} {spec['stage']} {spec['company']} {spec['team']} {domain_name(spec)}", image='serverless_cli')

  urls = re.findall(r" [-] https://[-\w.]+execute-api[-\w.]+/\w+/[\w-]+", log)
  for url in urls:
    m = re.match(r" - (https://[-\w.]+/\w+)/event-writer", url)
    if m:
      spec['endpoint_event_writer_api'] = m.group(1)
    else:
      m = re.match(r" - (https://[-\w.]+/\w+)/categories", url)
      if m:
        spec['endpoint_product_catalog_api'] = m.group(1)
      else:
        m = re.match(r" - (https://[-\w.]+/\w+)/sms", url)
        if m:
          spec['endpoint_photo_receive_api'] = m.group(1)

  logging.info(f"endpoint event writer={spec['endpoint_event_writer_api']}")
  logging.info(f"endpoint product catalog={spec['endpoint_product_catalog_api']}")
  logging.info(f"endpoint photo receive={spec['endpoint_photo_receive_api']}")


def invoke(spec):
  image_source_file = "benchmark_images/snowdrop.jpg"
  image_target_file = "benchmark_images/snowdrop-base64.jpg"
  encodeImage(image_source_file, image_target_file)

  envs = {
    'EVENT_WRITER_URL': spec['endpoint_event_writer_api'],
    'PRODUCT_CATALOG_URL': spec['endpoint_product_catalog_api'],
    'PHOTO_RECEIVE_URL': spec['endpoint_photo_receive_api'],
    'IMAGE_FILE': image_target_file
  }
  spec.run_k6(envs)


def cleanup(spec):
  # Empty web bucket used by backend photos service (2.receive) to store images for the frontend
  spec.run(f"aws s3 rm s3://{domain_name(spec)} --recursive", image='aws_cli')
  spec.run(f"./remove.sh {spec['region']} {spec['stage']} {spec['company']} {spec['team']} {domain_name(spec)}", image='serverless_cli')


# Util

def encodeImage(source_filename, target_filename):
  with open(source_filename, 'rb') as image:  # open binary file in read mode
    image_64_encode = base64.b64encode(image.read())
    with open(target_filename, "wb") as target_image_file:
      target_image_file.write(image_64_encode)


def domain_name(spec):
  return f"hello-retail-{spec['deploy_id']}"
