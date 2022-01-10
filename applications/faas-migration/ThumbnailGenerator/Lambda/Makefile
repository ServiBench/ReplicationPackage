IMAGE_BUCKET_NAME := stalluri-tgen-images
THUMB_BUCKET_NAME := stalluri-tgen-thumbnails
URL := https://2rn4r68uj1.execute-api.eu-central-1.amazonaws.com/dev
FILENAME := img.png

build:
	# maven:3.6.3-jdk-8-slim
	mvn clean install

deploy:
	# amaysim/serverless:2.0.0
	serverless deploy -v
	# Retrieve $URL after deployment!

run:
	# params:
	# $URL=https://nijl6ekboj.execute-api.us-east-1.amazonaws.com/dev/upload
	# $FILENAME=img.png => this should some kind of series to avoid conflicting file names
	cat ../test-images/test-1.png | base64 > ../test-images/test-1-base64
	k6 run -e "IMAGE_FILE=../test-images/test-1-base64" -e "URL=${URL}/upload?filename=${FILENAME}" load_script.js

test:
	# mikesir87/aws-cli:1.18.134
	aws s3 cp s3://${THUMB_BUCKET_NAME}/resized-${FILENAME} .
	cmp --silent resized-${FILENAME} ../test-images/test-1_thumbnail.png

clean:
	# mikesir87/aws-cli:1.18.134
	aws s3 rm s3://$(IMAGE_BUCKET_NAME) --recursive
	aws s3 rm s3://$(THUMB_BUCKET_NAME) --recursive
	# amaysim/serverless:2.0.0
	serverless remove -v
