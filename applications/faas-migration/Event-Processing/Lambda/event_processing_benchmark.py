import logging
# import os, sys
# optional Python client
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))    # add parent folder to path to access test_event_processing.py
# import test_event_processing

BENCHMARK_CONFIG = """
event_processing:
  description: Ingests, normalizes, and persists different event types. Uses SNS, SQS, and Aurora RDBMS.
  provider: aws
  region: us-east-1
  memory_size: 1024
  stage: dev
  root: ..
  workload_script: ../workload_script.js
"""


def prepare(spec):
    spec.run(f"npm install && {sls_cmd('deploy', spec)}", image='serverless_cli')
    spec['deployment_bucket'] = spec.run(sls_cmd('info', spec) + " | grep ServerlessDeploymentBucketName | awk '{print $2}'", image='serverless_cli').rstrip()
    spec['endpoint'] = spec.run(sls_cmd('info', spec) + " | grep ServiceEndpoint | awk '{print $2}'", image='serverless_cli').rstrip()
    logging.info(f"service endpoint={spec['endpoint']}")


def invoke(spec):
    envs = {
        'URL': spec['endpoint'] + '/'
    }
    spec.run_k6(envs)

    # NOTE: Alternative client implementation without sb integration with additional event validation after execution.
    # Usage: Need to enable transfer log in workload_script.js
    # count = 1
    # delay = 0
    # # Migrated Python client
    # test_event_processing.test(spec, spec['endpoint'], delay, count)
    # # Original go client
    # spec.run(f"go run ../test_event_processing.go -endpoint {spec['endpoint']} -count {count} -delay {delay}", image='golang')


def cleanup(spec):
    """Removing a VPC takes exceedingly long (~40 minutes).
    * Open issue: https://github.com/serverless/serverless/issues/5008
    * Forum discussion: https://forum.serverless.com/t/very-long-delay-when-doing-sls-remove-of-lambda-in-a-vpc/2535/5
    * Workaround didn't help: The plugin serverless-plugin-vpc-eni-cleanup (https://github.com/medikoo/serverless-plugin-vpc-eni-cleanup)
      couldn't fix the issue but rather introduced an infinite loop (describeNetworkInterfaces) in certain situations.
    """
    try:
        # First cleanup attempt may fail due to VPC dependency error when an AWS Firewall rule creates an external security group.
        spec.run(sls_cmd('remove', spec), image='serverless_cli', check=True)
    except Exception:
        logging.warn('First cleanup attempt failed, retrying ...')
        # Fixes VPC dependency error after deleting other resources
        # The managed security group would often get recreated during removal when cleaned up before.
        cleanup_security_group(spec)
        # Need to re-create the deployment bucket to fix idempotentcy issue of remove:
        # https://github.com/serverless/serverless/issues/3964
        create_bucket_cmd = f"aws s3api create-bucket --bucket {spec['deployment_bucket']} --region {spec['region']}"
        spec.run(create_bucket_cmd, image='aws_cli')
        # Retry cleanup
        spec.run(sls_cmd('remove', spec), image='serverless_cli')
        # Ensure deployment bucket gets deleted
        delete_bucket_cmd = f"aws s3 rb s3://{spec['deployment_bucket']} --force"
        spec.run(delete_bucket_cmd, image='aws_cli')


def cleanup_security_group(spec):
    """Deletes a AWS Firewall managed security group that prevents CloudFormation cleanup.
    This workaround fixes automated cleanup of this application in enterprise accounts where the AWS Firewall
    automatically creates a security group. This FMManaged caused a dependency error because it is referenced by
    the VPC of the application and CloudFormation doesn't delete externally created dependencies."""
    vpc_config = spec.run(f"{sls_cmd('info', spec)} | grep 'VpcId:'", image='serverless_cli').rstrip()
    vpc_id = vpc_config.replace('VpcId: ', '')
    sg_query_cmd = f"""aws ec2 describe-security-groups --filters "Name=vpc-id,Values={vpc_id}" "Name=tag-key,Values=FMManaged" --query "SecurityGroups[*].[GroupId]" --output text"""
    managed_sg = spec.run(sg_query_cmd, 'aws_cli').rstrip()
    if managed_sg:
        delete_cmd = f"aws ec2 delete-security-group --group-id {managed_sg}"
        spec.run(delete_cmd, 'aws_cli')


def sls_cmd(command, spec):
    """Returns a shell command string for a given Serverless Framework `command` in the given `spec` context.
    Configures environment variables (envs)."""
    envs = (
        f"STAGE={spec['stage']} "
        f"REGION={spec['region']} "
        f"MEMORY_SIZE={spec['memory_size']} "
    )
    # NOTE: prefix with "SLS_DEBUG=* " for debugging
    return f"{envs}serverless {command} --verbose"
