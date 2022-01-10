import logging
import random
from pathlib import Path
import base64
from io import BytesIO
from imageio import imread, imwrite
from skimage.util import random_noise


BENCHMARK_CONFIG = """
thumbnail_generator:
  description: Generates a thumbnail every time an image is uploaded to object storage.
  provider: aws
  stage: dev
  region: us-east-1
  memory_size: 1024
  root: ..
  num_different_images: 1
"""


def prepare(spec):
    # The deploy_id is used to generate globally unique S3 bucket names
    spec['deploy_id'] = spec['deploy_id'] or random.randint(1000, 9999)
    spec.run('mvn clean install', image='maven:3.6.3-jdk-8-slim')
    spec.run(sls_cmd('deploy', spec), image='serverless_cli')
    spec['endpoint'] = spec.run(sls_cmd('info', spec) + " | grep ServiceEndpoint | awk '{print $2}'", image='serverless_cli').rstrip()
    logging.info(f"endpoint={spec['endpoint']}")


def invoke(spec):
    # Number of images can be passed through spec later
    test_images_path = Path('../test-images')
    img_array = imread(test_images_path.joinpath('test-1.png'))
    for i in range(spec['num_different_images']):
        # Add random noise to image. Also remove alpha channel as JPEG doesn't support it
        noisy_img = random_noise(img_array)[:,:,:3]
        with BytesIO() as png_img:
            # Fails with imageio 2.11.0 released 2021-11-18 due to a regression:
            # https://github.com/imageio/imageio/issues/687#issuecomment-972616601
            # Workound pip install 'imageio==2.10.5'
            imwrite(png_img, noisy_img, format='jpg', quality=25)
            png_img.seek(0) # Reset position after writing
            # Prepare base64 encoded test image
            encoded_string = base64.b64encode(png_img.read())
            with open(test_images_path.joinpath(f"test-base64-{i}.jpg"), "wb") as target_image_file:
                target_image_file.write(encoded_string)

    envs = {
        'IMAGE_FILE_PREFIX': '../test-images/test-base64-',
        'NUM_IMAGES': spec['num_different_images'],
        'BASE_URL': spec['endpoint']
    }
    spec.run_k6(envs)


def cleanup(spec):
    spec.run(f"aws s3 rm s3://{image_bucket(spec)}/ --recursive", image='aws_cli')
    spec.run(f"aws s3 rm s3://{thumb_bucket(spec)}/ --recursive", image='aws_cli')
    spec.run(sls_cmd('remove', spec), image='serverless_cli')


def sls_cmd(command, spec):
    """Returns a shell command string for a given Serverless Framework `command` in the given `spec` context.
    Configures environment variables (envs)."""
    envs = (
        f"STAGE={spec['stage']} "
        f"REGION={spec['region']} "
        f"MEMORY_SIZE={spec['memory_size']} "
        f"IMAGE_BUCKET={image_bucket(spec)} "
        f"THUMB_BUCKET={thumb_bucket(spec)} "
    )
    return f"{envs}serverless {command} --verbose"


def image_bucket(spec):
    return f"thumbgen-images-sb-{spec['deploy_id']}"


def thumb_bucket(spec):
    return f"thumbgen-thumbnails-sb-{spec['deploy_id']}"
