# Practical Aspects of FaaS Applications' Migration - Go implementation

This repository contains all Go based implementations described in my Bachelor Thesis. These being the implementations for AWS Lambda and IBM Cloud Functions of the ToDo API use case. 

Apart from the regular requirements for the deployment on these Cloud Providers described in the [Main Code Repository](https://github.com/perfkit/faas-migration). These Implementations also need the Go SDK with at least version 1.11 or newer to be built.

## Getting the source code

To download the source code just run the following command:
```
go get -d github.com/anonymous/faas-migration-go/...
```

## Directories

This repository is grouped into three subdirectories:
- `aws`: Contains the AWS Lambda based implementation
- `ibm`: Contains the IBM Cloud Functions based implementation
- `core`: Contains a vendor unspecific and generic implementation of the functions behaviour

## Deploying

The deployment procedure differs for each implementation. Please look into the directory of the implementation for information on the procedure.

## Testing

The ToDo API can be tested using an executable. How this is specifically done can be found [here](https://github.com/c-mueller/faas-migration/tree/master/ToDo-API).

## License

The implementations shown here are Licensed under Apache License (Version 2.0)
