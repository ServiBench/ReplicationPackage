# Event Processing - IBM Implementation

## Requirements

Deploying this application requires the following dependencies and prerequisites:

- A CloudFoundry Organzation and space to deploy in
- IBM Cloud CLI with Cloud Functions extension
- GNU Make
- `jq`

Links to the tools mentioned here can be found in this [Document](/docs/tools.md)

## Deployment Guide

To deploy the use-case first modify the following lines in the `Makefile` accordingly to suit your environment.

```make
# Define the Name and Space of your Cloud Foundry organzation accordingly
# The Makefile assumes this namespace is selected using "ibmcloud fn property --namespace"
# and "ibmcloud targed" appropriately
CF_ORG_NAME := mymail@mymail.com
CF_ORG_SPACE := dev
```

After that make sure the `<Org>_<Space>` function namespace is the current namespace and also ensure the
same space is defined as Target (can be checked by running `ibmcloud target`)

Next we have to ensure all dependencies i.e. The database and the Event Streams instance (including its topics) are created. This is done by running

```bash
make create_resources
```

Next we deploy the Actions by running:

```bash
make deploy_actions
```

This step also handles packaging in dependency installation of the functions using `npm`

Next the triggers can be created using the following command

```bash
make create_triggers
```

After the trigger has been created we need to create rules to ensure Actions get triggered from the functions by running:

```
make create_rules
```

Finally run `make create_api` to dpeloy the API mappings.

## Removing the Application

The services, triggers, API mappings and actions created for this application have to be removed manually. For example, using the Web UI.
