#############################################################################
######## CONFIGURATION (DONE IN THE BENCHMARK) ##############################
#############################################################################

# Define The name of the Resource Group to deploy in (must exist)
RESOURCE_GROUP_NAME := faas-migration
# Define the name of the storage account (gets created if not present)
STORAGE_ACCOUNT_NAME := cmuellertodostore
# Define the Name of the Function App (gets created if not present)
FUNCTION_APP_NAME := cmueller-bt-todo-api
# Define the name of the Application insights instance used for tracing/logging (gets created if not present)
APPINSIGHTS_NAME := cmuellertodoai
# Set the name of your preferred region e.g. westeurope, westus...
AZURE_REGION := eastus

#############################################################################
######## DO NOT MODFY CODE BELOW. UNLESS YOU KNOW WHAT YOU'RE DOING! ########
#############################################################################

create_storage_account:
	func init --worker-runtime dotnet --force
	az group create -l $(AZURE_REGION) -n $(RESOURCE_GROUP_NAME)
	az storage account create -g $(RESOURCE_GROUP_NAME) -n $(STORAGE_ACCOUNT_NAME) --kind StorageV2 --sku Standard_LRS --location $(AZURE_REGION)

update_credentials: CONNECTION_STRING := `az storage account show-connection-string --name $(STORAGE_ACCOUNT_NAME) | jq -r '.connectionString'`
update_credentials:
	jq ".Values.AzureWebJobsStorage = \"$(CONNECTION_STRING)\"" local.settings.json > temp
	mv temp local.settings.json

init: create_storage_account update_credentials

build: clean
	dotnet publish todo-api.sln

run_local: init build
	func host start

create_function_app:
	az configure --defaults location=$(AZURE_REGION)
	az resource create -g $(RESOURCE_GROUP_NAME) -n $(APPINSIGHTS_NAME) --resource-type "Microsoft.Insights/components" --properties "{\"Application_Type\":\"web\"}"
	az functionapp create -g $(RESOURCE_GROUP_NAME) -n $(FUNCTION_APP_NAME) --storage-account $(STORAGE_ACCOUNT_NAME) --consumption-plan-location $(AZURE_REGION) --app-insights $(APPINSIGHTS_NAME) --runtime dotnet --functions-version 2 

# Probably trying to mitigate the error "Timed out waiting for SCM to update the Environment Settings"
# see https://github.com/Azure/azure-functions-core-tools/issues/1863
sleep:
	sleep 20

deploy: init create_function_app build sleep
	func azure functionapp publish $(FUNCTION_APP_NAME) --csharp --force > prepare_log.txt

clean:
	rm -rvf bin/
	rm -rvf obj/
	rm -f Azure.csproj 
# rm -f Azure.csproj  to avoid the confusion with todo-api.csproj
cleanup:
	az resource delete \
  --resource-group $(RESOURCE_GROUP_NAME) \
  --name $(APPINSIGHTS_NAME) \
  --resource-type "Microsoft.Insights/components"
	az functionapp delete --name $(FUNCTION_APP_NAME) --resource-group $(RESOURCE_GROUP_NAME)
	az storage account delete -g $(RESOURCE_GROUP_NAME) -n $(STORAGE_ACCOUNT_NAME) --yes
	az group delete --name $(RESOURCE_GROUP_NAME) --yes
	rm -rvf out/
	rm -f host.json
	rm -f local.settings.json
	rm -f prepare_log.txt
