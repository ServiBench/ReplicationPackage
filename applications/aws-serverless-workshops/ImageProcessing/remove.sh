#!/bin/sh

# Parameters
region=$1
deployId=$2

# Variables (duplicates in setup.sh)
IMAGE_MAGICK_STACK_NAME="image-magick-cf-sb-${deployId}"
DEPLOYMENT_BUCKET_NAME="wildrydes-deployment-sb-${deployId}"
SFN_NAME="wildrydes-sfn-module-sb-${deployId}"

aws --region ${region} cloudformation delete-stack --stack-name wildrydes
aws --region ${region} cloudformation wait stack-delete-complete --stack-name wildrydes
aws s3 rm s3://${SFN_NAME} --recursive
aws s3 rm s3://${DEPLOYMENT_BUCKET_NAME} --recursive
aws --region ${region} rekognition delete-collection --collection-id rider-photos
aws s3 rb s3://${DEPLOYMENT_BUCKET_NAME}
aws s3 rb s3://${SFN_NAME}
aws --region ${region} cloudformation delete-stack --stack-name serverlessrepo-${IMAGE_MAGICK_STACK_NAME}

# finally delete all log groups resulting from this task (not done autimatically!)
aws --region ${region} logs describe-log-groups --log-group-name-prefix /aws/lambda/wildrydes | grep -o '"/aws/lambda/wildrydes.*"' | cut -d '"' -f 2 | \
  while read logGroup
  do
    aws --region ${region} logs delete-log-group --log-group-name $logGroup
  done
