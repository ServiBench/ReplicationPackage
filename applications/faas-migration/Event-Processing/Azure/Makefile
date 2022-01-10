# CONFIGURATION

# General Azure Configuration
RESOURCE_GROUP_NAME := faas-migration
AZURE_REGION := westeurope

# MySQL Configuration
MYSQL_ADMIN_USERNAME := krnladmin
MYSQL_ADMIN_PASSWORD := eSh4iimaeh2lioxaseukiegheNoo4phi
MYSQL_SERVER_NAME := krnlevtprocdb
MYSQL_DB_NAME := krnlevtprocdb

# Other Azure Component Configuration
STORAGE_ACCOUNT_NAME := krnlevtprocstore
APPINSIGHTS_NAME := krnlfuncai
FUNCTION_APP_NAME := krnlfuncapp
EVT_HUB_NAME := krnlevthub

########################################################################################################

# CONFIG DERIVATIONS
MYSQL_HOSTNAME := $(MYSQL_SERVER_NAME).mysql.database.azure.com
MYSQL_USERNAME := $(MYSQL_ADMIN_USERNAME)@$(MYSQL_SERVER_NAME)

# MAKEFILE

create_storage_account:
	echo Creating Storage Account...
	az storage account create -g $(RESOURCE_GROUP_NAME) -n $(STORAGE_ACCOUNT_NAME) --kind StorageV2 --sku Standard_LRS --location $(AZURE_REGION)

create_mysql:
	echo Creating MySQL instance
	az mysql server create -g $(RESOURCE_GROUP_NAME) -n $(MYSQL_SERVER_NAME) -u $(MYSQL_ADMIN_USERNAME) -p $(MYSQL_ADMIN_PASSWORD) -l $(AZURE_REGION) --sku-name B_Gen5_2
	az mysql db create -g $(RESOURCE_GROUP_NAME) --server-name $(MYSQL_SERVER_NAME) -n $(MYSQL_DB_NAME)
	# Create a Grant all Firewall rule to allow access from outside of azure
	az mysql server firewall-rule create -g $(RESOURCE_GROUP_NAME) --server-name $(MYSQL_SERVER_NAME) --name allow-all --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255

create_service_bus:
	echo Creating EventHub Namespace
	az servicebus namespace create -g $(RESOURCE_GROUP_NAME) -n $(EVT_HUB_NAME) --location $(AZURE_REGION)
	echo Creating Topics and subscriptions
	echo Creating Topic 'forecast'
	az servicebus topic create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) -n forecast
	az servicebus topic subscription create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) --topic-name forecast -n forecastpush
	az servicebus topic subscription create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) --topic-name forecast -n forecastpull
	echo Creating Topic 'temperature'
	az servicebus topic create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) -n temperature
	az servicebus topic subscription create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) --topic-name temperature -n temperaturepush
	az servicebus topic subscription create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) --topic-name temperature -n temperaturepull
	echo Creating Topic 'statechange'
	az servicebus topic create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) -n statechange
	az servicebus topic subscription create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) --topic-name statechange -n statechangepush
	az servicebus topic subscription create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) --topic-name statechange -n statechangepull
	echo Creating Queue
	az servicebus queue create -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) -n output

create_function_app:
	echo Creating Webapp and Insights
	az resource create -g $(RESOURCE_GROUP_NAME) -n $(APPINSIGHTS_NAME) --resource-type "Microsoft.Insights/components" --properties '{"Application_Type":"web"}'
	az functionapp create -g $(RESOURCE_GROUP_NAME) -n $(FUNCTION_APP_NAME) --storage-account $(STORAGE_ACCOUNT_NAME) --consumption-plan-location $(AZURE_REGION) --app-insights $(APPINSIGHTS_NAME) --runtime node

create_resources: create_storage_account create_mysql create_service_bus

create_config: STORAGE_ACCOUNT_CONNECTION_STRING := `az storage account show-connection-string --name $(STORAGE_ACCOUNT_NAME) | jq -r '.connectionString'`
create_config: SERVICE_BUS_CONNECTION_STRING := `az servicebus namespace authorization-rule keys list -g $(RESOURCE_GROUP_NAME) --namespace-name $(EVT_HUB_NAME) --name RootManageSharedAccessKey | jq -r '.primaryConnectionString'`
create_config: create_resources
	echo "Writing local manifest"
	cp local.settings.json.template local.settings.json
	jq ".Values.AzureWebJobsStorage = \"$(STORAGE_ACCOUNT_CONNECTION_STRING)\"" local.settings.json | sponge local.settings.json
	jq ".Values.ServiceBusConnection = \"$(SERVICE_BUS_CONNECTION_STRING)\"" local.settings.json | sponge local.settings.json
	jq ".ConnectionStrings.ServiceBusConnection = \"$(SERVICE_BUS_CONNECTION_STRING)\"" local.settings.json | sponge local.settings.json
	jq ".Values.DBName = \"$(MYSQL_DB_NAME)\"" local.settings.json | sponge local.settings.json
	jq ".Values.DBEndpoint = \"$(MYSQL_HOSTNAME)\"" local.settings.json | sponge local.settings.json
	jq ".Values.DBUsername = \"$(MYSQL_USERNAME)\"" local.settings.json | sponge local.settings.json
	jq ".Values.DBPassword = \"$(MYSQL_ADMIN_PASSWORD)\"" local.settings.json | sponge local.settings.json

install:
	npm install

run_local: create_config install
	func host start

deploy: create_config create_function_app install
	func azure functionapp publish $(FUNCTION_APP_NAME)
	func azure functionapp publish $(FUNCTION_APP_NAME) -o

update: install
	func azure functionapp publish $(FUNCTION_APP_NAME)
	func azure functionapp publish $(FUNCTION_APP_NAME) -o