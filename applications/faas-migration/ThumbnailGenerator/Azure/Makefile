# Configuration
RESOURCE_GROUP := faas-migration
# The function app name needs to be unique globally!
FUNCTION_APP_NAME := cmueller-bt-thumbnail-generator
REGION := westeurope
FILENAME := img.png

# Do not change from here
# see versions: https://mcr.microsoft.com/v2/azure-cli/tags/list
# overview of runtimes: https://hub.docker.com/_/microsoft-dotnet-core/
# mcr.microsoft.com/azure-cli:2.9.1
# NOTE: the functions extension also requires dotnet on your path (i.e., not explicitly mentioned as requirement, installed through brew cask install dotnet). The project file says .NET version  2.0
# => MAYBE something alike mcr.microsoft.com/dotnet/core/sdk:2.0
STORAGE_ACCOUNT_CONNECTION_STRING := `az functionapp config appsettings list -g $(RESOURCE_GROUP) -n $(FUNCTION_APP_NAME) | jq -r '.[] | select(.name == "AzureWebJobsStorage") | .value'`
build:
	# maven:3.6.3-jdk-8-slim
	# mcr.microsoft.com/azure-cli:2.9.1
	# NEEDS both because it checks for Azure Functions Core Tools updates during the last build step
	APP_NAME=$(FUNCTION_APP_NAME) RG=$(RESOURCE_GROUP) AZ_REGION=$(REGION) mvn clean install

publish: build
	# maven:3.6.3-jdk-8-slim
	APP_NAME=$(FUNCTION_APP_NAME) RG=$(RESOURCE_GROUP) AZ_REGION=$(REGION) mvn azure-functions:deploy

deploy: publish
	# mcr.microsoft.com/azure-cli:2.9.1
	az storage container create -n output --connection-string $(STORAGE_ACCOUNT_CONNECTION_STRING)
	az storage container create -n input --connection-string $(STORAGE_ACCOUNT_CONNECTION_STRING)

list:
	az functionapp show -g $(RESOURCE_GROUP) -n $(FUNCTION_APP_NAME)

run:
	# params:
	# $URL=https://<FunctionApp Name>.azurewebsites.net/api/Upload-Image?name=<FileNameInBlobStorage>
	# => derived from $FUNCTION_APP_NAME
	# $FILENAME=<FileNameInBlobStorage>
	cat ../test-images/test-1.png | base64 | curl -v -d @- "https://$(FUNCTION_APP_NAME).azurewebsites.net/api/Upload-Image?name=$(FILENAME)"

test:
	# mcr.microsoft.com/azure-cli:2.9.1
	# params: ${FILE}
	az storage blob download --container-name output --connection-string $(STORAGE_ACCOUNT_CONNECTION_STRING) --name $(FILENAME) --file ./$(FILENAME)
	cmp --silent $(FILENAME) ../test-images/test-1_thumbnail.png

clean:
	# mcr.microsoft.com/azure-cli:2.9.1
	az group delete --name $(RESOURCE_GROUP) --yes

run_local: build
	echo "{}" > local.settings.json
	func azure functionapp fetch-app-settings $(FUNCTION_APP_NAME)
	APP_NAME=$(FUNCTION_APP_NAME) RG=$(RESOURCE_GROUP) AZ_REGION=$(REGION) mvn azure-functions:run

ls_input:
	az storage blob list --container-name input --connection-string $(STORAGE_ACCOUNT_CONNECTION_STRING) | jq '.[] | {file_name: .name, file_size: .properties.contentLength,creation_timestamp: .properties.creationTime}'

ls_output:
	az storage blob list --container-name output --connection-string $(STORAGE_ACCOUNT_CONNECTION_STRING) | jq '.[] | {file_name: .name, file_size: .properties.contentLength,creation_timestamp: .properties.creationTime}'

# Just some random test stuff:
# this is available from GNU make 3.81 (see https://stackoverflow.com/a/23845391/6875981)
var_test: export MY_VAR=abcd
var_test:
	echo ${MY_VAR}
	echo ${STORAGE_ACCOUNT_CONNECTION_STRING}
