# ToDo API - IBM Implementation

## Prerequisites

Deploying this use case requires the following tools:
- GNU make
- `jq`
- `sponge` command
- Go SDK Version 1.11 or newer
- IBM Cloud CLI with Cloud Functions extension

You also need a CloudFoundry Space to be set as the current space of the `ibmcloud fn` CLI this is done by setting it using `bmcloud fn property set --namespace <Space Name>`. Because this uses a Cloudant Lite instance by default you should also make sure you have no other cloudant Lite instance deployed. Otherwise you can change the `Makefile` to use a different plan.

## Deployment

### Step 1: (Optional) Configure Makefile

You might want to modify the name or the service plan of the database. This can be done by updating the `Makefile`:

```Makefile
########################################
### CONFIGURATION                    ###
########################################

# Define the name of the Cloudant Database
CLOUDANT_INSTANCE_NAME := todo-cloudant-db
# Define the name of the cloudant access key
CLOUDANT_ACCESS_KEY_NAME := access-key
# Set the instance plan type
CLOUDANT_INSTANCE_PLAN := Lite
```

### Step 2: Creating the Cloudant Instance and retrieving credentials

To deploy the cloudant instance just run the following command:
```bash
make build_creds
```

after that you might want to wait for a bit before going to the next step.

### Step 3: Deploying the actions

To deploy the actions just run the following command:
```bash
make deploy_actions
```

This will compile the sources and publish them on IBM Cloud

### Step 4: Creating the Database

To create the database within the cloudant instance run:
```bash
make create_database
```

### Step 5: Create the API Mappings

The API Mappings can get created by running the `make deploy_api` command. When the deployment is done this should return a list of exposed endpoints. Similar to this one:
```
Action: /kaffemuehle@posteo.de_dev/todo-del
   API Name: /todo
   Base path: /todo
   Path: /del
   Verb: post
   URL: https://service.eu-de.apiconnect.ibmcloud.com/gws/apigateway/api/c60a759fd5d12c47c388136b8cf911591d1796f1df45943fd4db770d20111187/todo/del
Action: /kaffemuehle@posteo.de_dev/todo-done
   API Name: /todo
   Base path: /todo
   Path: /done
   Verb: post
   URL: https://service.eu-de.apiconnect.ibmcloud.com/gws/apigateway/api/c60a759fd5d12c47c388136b8cf911591d1796f1df45943fd4db770d20111187/todo/done
Action: /kaffemuehle@posteo.de_dev/todo-get
   API Name: /todo
   Base path: /todo
   Path: /get
   Verb: get
   URL: https://service.eu-de.apiconnect.ibmcloud.com/gws/apigateway/api/c60a759fd5d12c47c388136b8cf911591d1796f1df45943fd4db770d20111187/todo/get
Action: /kaffemuehle@posteo.de_dev/todo-lst
   API Name: /todo
   Base path: /todo
   Path: /lst
   Verb: get
   URL: https://service.eu-de.apiconnect.ibmcloud.com/gws/apigateway/api/c60a759fd5d12c47c388136b8cf911591d1796f1df45943fd4db770d20111187/todo/lst
Action: /kaffemuehle@posteo.de_dev/todo-put
   API Name: /todo
   Base path: /todo
   Path: /put
   Verb: post
   URL: https://service.eu-de.apiconnect.ibmcloud.com/gws/apigateway/api/c60a759fd5d12c47c388136b8cf911591d1796f1df45943fd4db770d20111187/todo/put
```

The rootpath used for testing here is everything before (and including) `/todo`

## Updating

To update the deployment when developing just run:
```
make update
```

It is important to mention that this will cause an endpoint change since we have to recreate the API every time we update the action.