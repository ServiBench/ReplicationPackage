#############################################################################
######## CONFIGURATION ######################################################
#############################################################################

# Define The name of the Resource Group to deploy in (must exist)
RESOURCE_GROUP_NAME := faas-migration
# Define the name of the storage account (gets created if not present)
STORAGE_ACCOUNT_NAME := cmuellermtrxmulstore
# Define the Name of the Function App (gets created if not present)
FUNCTION_APP_NAME := cmuellermatrixmul
# Define the name of the Application insights instance used for tracing/logging (gets created if not present)
APPINSIGHTS_NAME := cmuellermatrixmulai
# Set the name of your preferred region e.g. westeurope, westus...
AZURE_REGION := westeurope

#############################################################################
######## DO NOT MODFY CODE BELOW. UNLESS YOU KNOW WHAT YOU'RE DOING! ########
#############################################################################

create_storage_account:
	az storage account create -g $(RESOURCE_GROUP_NAME) -n $(STORAGE_ACCOUNT_NAME) --kind StorageV2 --sku Standard_LRS --location $(AZURE_REGION)

update_credentials: CONNECTION_STRING := `az storage account show-connection-string --name $(STORAGE_ACCOUNT_NAME) | jq -r '.connectionString'`
update_credentials:
	jq ".Values.AzureWebJobsStorage = \"$(CONNECTION_STRING)\"" local.settings.json | sponge local.settings.json

init: create_storage_account update_credentials

build: clean
	dotnet publish

run_local: init build
	func host start

create_function_app:
	az resource create -g $(RESOURCE_GROUP_NAME) -n $(APPINSIGHTS_NAME) --resource-type "Microsoft.Insights/components" --properties '{"Application_Type":"web"}'
	az functionapp create -g $(RESOURCE_GROUP_NAME) -n $(FUNCTION_APP_NAME) --storage-account $(STORAGE_ACCOUNT_NAME) --consumption-plan-location $(AZURE_REGION) --app-insights $(APPINSIGHTS_NAME) --runtime dotnet

sleep_20:
	sleep 20

deploy: init create_function_app build sleep_20
	func azure functionapp publish $(FUNCTION_APP_NAME)
	func azure functionapp publish $(FUNCTION_APP_NAME) -o

clean:
	rm -rvf bin/
	rm -rvf obj/
	
