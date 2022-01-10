#!/bin/sh

# Parameters
region=$1
deployId=$2

# Variables
IMAGE_MAGICK_ARN="arn:aws:serverlessrepo:us-east-1:145266761615:applications/image-magick-lambda-layer"
CS_NAME="sb-${deployId}-im-change-set"
# Duplicates in remove.sh
IMAGE_MAGICK_STACK_NAME="image-magick-cf-sb-${deployId}"
DEPLOYMENT_BUCKET_NAME="wildrydes-deployment-sb-${deployId}"
SFN_NAME="wildrydes-sfn-module-sb-${deployId}"

aws --region ${region} serverlessrepo create-cloud-formation-change-set --application-id ${IMAGE_MAGICK_ARN} --stack-name ${IMAGE_MAGICK_STACK_NAME} --change-set-name ${CS_NAME}
aws --region ${region} cloudformation wait change-set-create-complete --change-set-name ${CS_NAME} --stack-name serverlessrepo-${IMAGE_MAGICK_STACK_NAME}
aws --region ${region} cloudformation execute-change-set --change-set-name ${CS_NAME} --stack-name serverlessrepo-${IMAGE_MAGICK_STACK_NAME}
aws --region ${region} cloudformation describe-stacks --stack-name serverlessrepo-${IMAGE_MAGICK_STACK_NAME} --query "Stacks[0].Outputs[0].OutputValue" --output text

aws --region ${region} rekognition create-collection --collection-id rider-photos
aws --region ${region} s3 mb s3://${DEPLOYMENT_BUCKET_NAME}
aws --region ${region} s3 mb s3://${SFN_NAME}
aws --region ${region} s3 sync test-images s3://${SFN_NAME}/test-images

cd src/lambda-functions/thumbnail
npm install
cd ../face-detection
npm install
cd ../mock-notification
npm install
cd ../face-search
npm install
cd ../index-face
npm install
cd ../persist-metadata
npm install

cd ../../cloudformation
aws --region ${region} cloudformation package \
      --template-file module-setup.yaml \
      --output-template-file template.packaged.yaml \
      --s3-bucket ${DEPLOYMENT_BUCKET_NAME} \
      --s3-prefix ImageProcessing
aws --region ${region} cloudformation deploy \
      --template-file template.packaged.yaml \
      --stack-name wildrydes \
      --capabilities CAPABILITY_IAM \
      --parameter-overrides TestImagesBucket=${SFN_NAME}
cd ../..

# Collect output
APIURL=$(aws --region ${region} cloudformation describe-stacks --stack-name wildrydes --query "Stacks[0].Outputs[5].OutputValue" --output text)
STATEMACHINEARN=$(aws --region ${region} cloudformation describe-stacks --stack-name wildrydes --query "Stacks[0].Outputs[7].OutputValue" --output text)
BUCKETNAME=$(aws --region ${region} cloudformation describe-stacks --stack-name wildrydes --query "Stacks[0].Outputs[8].OutputValue" --output text)

# echo config
echo -e "\n${APIURL}\n${STATEMACHINEARN}\n${BUCKETNAME}"
