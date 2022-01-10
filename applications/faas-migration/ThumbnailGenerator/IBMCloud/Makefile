# STATUS: Started updating for new non-experimental trigger.
# Ran into some issue due to creating multiple service instances
# so the IAM policy subsequently failed.
# Also need to figure out the right command for binding the changes package.

# Defines the name of the input bucket used to upload Images to
OBJECT_STORAGE_INPUT_BUCKET := krnl-tgen-uss
# Defines the name of the output bucket used to thumbnails to
OBJECT_STORAGE_OUTPUT_BUCKET := krnl-tgen-uss-thumbnails
# Access Key to Object Storage with Manager Permissions
OBJECT_STORAGE_ACCESS_KEY := 83233f26ea46473189aca35dc634ca63
# Secret Key to Object Storage with Manager Permissions
OBJECT_STORAGE_SECRET_KEY := d06b121718b21dbe694fb2be6963d91137b47c884040adf1

# Defines the Endpoint used to Access the data. Usualy this should not be changed
OBJECT_STORAGE_ENDPOINT := s3.us-south.cloud-object-storage.appdomain.cloud

# NAME DEFINITION
NAMESPACE_NAME := tgen-uss
COS_SERVICE_NAME := $(NAMESPACE_NAME)-k7
PACKAGE_BINDING_NAME := tgen-os-binding
TRIGGER_NAME := tgen-os-trigger
RULE_NAME := tgen-os-rule
UPLOADER_ACTION_NAME := uploader
GENERATOR_ACTION_NAME := generator

# DOCS:
# COS trigger functions example: https://github.com/IBM/cos-trigger-functions
# => NOTE: "This trigger is currently available in us-south, us-east, and eu-gb regions."

# Portal:
# Functions: https://cloud.ibm.com/functions/
# Object Storage: https://cloud.ibm.com/objectstorage

# COS authentication: https://cloud.ibm.com/docs/cloud-object-storage?topic=cloud-object-storage-uhc-hmac-credentials-main
# COS CLI: https://github.com/IBM/ibmcloud-cos-cli
# COS CLI docs: https://cloud.ibm.com/docs/cloud-object-storage?topic=cloud-object-storage-cli-plugin-ic-cos-cli

# MAKEFILE OPERATIONS

abc:
	# MALFORMED request:
	ibmcloud fn package bind /whisk.system/cos/changes $(PACKAGE_BINDING_NAME)

# ibmcom/ibm-cloud-developer-tools-amd64:1.1.0
# with plugin: ibmcloud plugin install cloud-object-storage
create_storage:
	ibmcloud resource service-instance-create $(COS_SERVICE_NAME) cloud-object-storage lite global

	ibmcloud resource service-instance 'tgen-uss-k7' --output json | jq '.[0] | .guid'
	# Somehow only reads it from stdin => need to pipe it :(
	ibmcloud cos config crn

	ibmcloud cos bucket-create --bucket krnl-tgen-uss --region us-south --output json
	ibmcloud cos bucket-create --bucket krnl-tgen-uss-thumbnails --region us-south --output json

	ibmcloud resource service-key-create hmac_cos_key Writer --instance-name $(COS_SERVICE_NAME) --parameters '{"HMAC":true}'

# IAM authentication somehow didn't work as some commands (e.g., bind) complained about missing credentials although
# the CRN id was set in the client accordingly: https://cloud.ibm.com/docs/cloud-object-storage?topic=cloud-object-storage-cli-plugin-ic-cos-cli
config_hmac_credentials:
	ibmcloud resource service-key-create hmac_cos_key Writer --instance-name $(COS_SERVICE_NAME) --parameters '{"HMAC":true}'
	ibmcloud cos config hmac
	# interactively enter access and secret key (separated by newlines)
	ibmcloud cos config auth
	# type the number '2' to switch to HMAC authentication (instead of IAM)
	# Bind credentials to service
	ibmcloud fn service bind cloud-object-storage cloud-object-storage --instance $(COS_SERVICE_NAME)

# ibmcom/ibm-cloud-developer-tools-amd64:1.1.0
init:
	# Change Region to Dallas
	ibmcloud target -r us-south
	ibmcloud target -r us-south --cf
	# Create New Namespace (run only once!)
	ibmcloud fn namespace create $(NAMESPACE_NAME)
	ibmcloud fn property set --namespace $(NAMESPACE_NAME)
	# NOT experimental anymore. See docs: https://github.com/IBM/cos-trigger-functions
	# Create IAM policy
	# FAILED: Multiple service instance with the same name 'tgen-uss' were found.
	ibmcloud iam authorization-policy-create functions cloud-object-storage "Notifications Manager" --source-service-instance-name $(NAMESPACE_NAME) --target-service-instance-name $(COS_SERVICE_NAME)
	
	ibmcloud fn package update cloud-object-storage --param endpoint $(OBJECT_STORAGE_ENDPOINT)
	ibmcloud fn service bind cloud-object-storage cloud-object-storage --instance $(COS_SERVICE_NAME)

	# Create package binding for object storage trigger
	ibmcloud fn package bind /whisk.system/cos/changes $(PACKAGE_BINDING_NAME)

	# # Create Package Binding for experimental object storage trigger
	# ibmcloud fn package bind /whisk.system/cos-experimental $(PACKAGE_BINDING_NAME)
	# # Bind service to function namespace
	# ibmcloud fn service bind cloud-object-storage $(PACKAGE_BINDING_NAME)

# maven:3.6.3-jdk-8-slim
build:
	# Build JAR
	mvn clean package

configure_trigger:
	ibmcloud fn trigger create $(TRIGGER_NAME) --feed $(PACKAGE_BINDING_NAME)/changes -p bucket $(OBJECT_STORAGE_INPUT_BUCKET) -p endpoint $(OBJECT_STORAGE_ENDPOINT)

deploy_actions: build
	ibmcloud fn action create $(UPLOADER_ACTION_NAME) target/thumbnail-generator.jar --web true --main spblab.thumbgen.wsk.Uploader -p endpoint $(OBJECT_STORAGE_ENDPOINT) -p bucket $(OBJECT_STORAGE_INPUT_BUCKET) -p access_key $(OBJECT_STORAGE_ACCESS_KEY) -p secret_key $(OBJECT_STORAGE_SECRET_KEY) -a final true
	ibmcloud fn action create $(GENERATOR_ACTION_NAME) target/thumbnail-generator.jar --main spblab.thumbgen.wsk.Generator -p endpoint $(OBJECT_STORAGE_ENDPOINT) -p output_bucket $(OBJECT_STORAGE_OUTPUT_BUCKET) -p access_key $(OBJECT_STORAGE_ACCESS_KEY) -p secret_key $(OBJECT_STORAGE_SECRET_KEY)

update_actions: build
	ibmcloud fn action update $(UPLOADER_ACTION_NAME) target/thumbnail-generator.jar --web true --main spblab.thumbgen.wsk.Uploader -p endpoint $(OBJECT_STORAGE_ENDPOINT) -p bucket $(OBJECT_STORAGE_INPUT_BUCKET) -p access_key $(OBJECT_STORAGE_ACCESS_KEY) -p secret_key $(OBJECT_STORAGE_SECRET_KEY) -a final true
	ibmcloud fn action update $(GENERATOR_ACTION_NAME) target/thumbnail-generator.jar --main spblab.thumbgen.wsk.Generator -p endpoint $(OBJECT_STORAGE_ENDPOINT) -p output_bucket $(OBJECT_STORAGE_OUTPUT_BUCKET) -p access_key $(OBJECT_STORAGE_ACCESS_KEY) -p secret_key $(OBJECT_STORAGE_SECRET_KEY)

register_rule:
	ibmcloud fn rule create $(RULE_NAME) $(TRIGGER_NAME) $(GENERATOR_ACTION_NAME)