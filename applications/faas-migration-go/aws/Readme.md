# ToDo API - AWS Implementation

This is the AWS implementation of the ToDo API Use-Case.

To build/deploy this implementation please ensure the following tools are installed and configured:
- Serverless Framework CLI
- Go SDK - Version 1.11 or newer
- GNU Make

## Building

To build the functions just run:
```
make build
```

## Deployment

To deploy them just run:
```
make deploy
```

This will also build the functions. Making the execution of `make build` beforehand unnecessary.

The endpoints are displayed once the deployment is done.

## Destroying / Removing

To destroy/remove the Deployment run:
```
make destroy
```
