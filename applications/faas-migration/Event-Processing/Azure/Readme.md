# Event-Processing - Azure Implementation

## Prerequisites

Environmental dependencies:

- Linux based environment (others are untested)
- `jq`
- GNU make
- Azure CLI (Logged In)
- Azure Functions Core Tools CLI
- NodeJS Version 8 or newer

Links to the tools mentioned here can be found in this [Document](/docs/tools.md)

Other dependencies:

- An Azure resource group to be used for deployment. This group has to exist before the deployment happens.

## Deployment

First modify the configuration section of the `Makefile` to suit your needs. Since some names like the
MySQL server name, storage account name and the function app name have to be unique across all Azure tenants it is recommended to modify these to prevent collisions.
It might also be a good idea to change the database pasword and username. But keep in mind the usernames allowed are restricted and names like `admin` or `root` are reserved and cannot be used.

```makefile
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
```

Once the modifications are done you can run the following command to deploy the functions and create the required services:

```bash
make deploy
```

to update the Source Code of the function app it is not necessary to run the service creation again. Instead just run the following command:

```bash
make update
```

Once Deployed the function app can be accessed using the following URL:
```
https://<FUNCTION_APP_NAME>.azurewebsites.net/api
```
This endpoint can be used to run the tests or to connect to the API manually

If you only want to create the services on azure and run the functions locally using the function host just run

```bash
make run_local
```

If the services do not get changed (i.e. deleted) you can run `func host start` to run the functions locally.

## Destroying the Deployment

See [here](/docs/azure_deploy.md) for more details.
