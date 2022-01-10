# Practical Aspects of FaaS Applications' Migration - Implemtentations

## General Documentation

Some general notes on configuring the cloud providers command line interfaces or the general deployment of a .NET based Function
Application on Azure can be found in the [Docs Folder](/docs).

## Prerequisites

The following section lists all prerequisites for the implementations based on the cloud provider.
The deployment guides are only tested on a Linux based enviornment.However they should work on MacOS without modifications since the `moreutils` package is available there using Homebrew ([See here](https://rentes.github.io/unix/utilities/2015/07/27/moreutils-package/)).

Running on Windows is more difficult because GNU `make` and `moreutils` are not directly available for Windows. Using [Cygwin](https://cygwin.com/index.html) might be an option though. Another approach could be the use of [WSL (Windows Subsystem for Linux)](https://docs.microsoft.com/en-us/windows/wsl/install-win10).

Links to the tools listed here can be found [here](docs/tools.md)

### AWS

To deploy to AWS using the deployment scripts you need:

- NodeJS - Version 8 or later
- Python 2.6.5+ or Python 3.3+
- AWS CLI
- Serverless Framework CLI
- GNU `make`
- `yq` utility

In the deployment guides we assume your local AWS CLI is authenticated and has sufficent IAM roles. [Click here](docs/aws_setup.md) to see wich roles we assigned to test the deployment.

### Microsoft Azure

To deploy to Microsoft Azure using the deployment scripts you need:

- NodeJS - Version 8 or later
- Python 2.7+ or Python 3.4+
- Azure CLI
- Azure Functions Core Tools
- GNU `make`
- `jq` Utility
- `sponge` Utility

The deployment guides assume that you are logged into the Azure CLI using `az login`

### IBM Cloud

To deploy to IBM Cloud using the deployment scripts you need:

- IBM Cloud CLI
    - `cloud-functions` extension
    - `event-streams` extension
- OpenWhisk Composer Tools
- GNU `make`
- `jq` Utility
- `sponge` Utility

Most of the IBM Cloud implementations requrie a CloudFoundry based Function namespace. We therefore assume that you are authenticated in the IBM Cloud CLI using the `ibmcloud login` command and we assume that you are targeting the CloudFoundry based function namespace using `ibmcloud target --cf -o <org> -s <space>` and `ibmcloud fn property --namespace <org>_<space>`.

Only the Thumbnail Generator uses an IAM based Namesapce because this makes a region change easier.

### Use Case Dependencies

These programms and SDKs are required to build the applications.

- NodeJS Version 8 or Newer
- .NET Framework SDK Version 2.1 or newer
- Go SDK Version 1.11 or newer
- Java 8 JDK

### Test Dependencies

To work with the testing guides the following utilites should be installed:

- Go SDK Version 1.11 or newer
- `curl` Utility
- `jq` Utility

### Development Environments

To implement the use-cases we have used the following IDEs:

- Visual Studio Code for JavaScript and  generic Editing
- JetBrains Rider for .NET
- JetBrains GoLand for Go
- JetBrains IntelliJ IDEA Community Edition for Java

## Directory Structure

The Use-Cases are grouped together in a Directory in the Root Directory. In the Directory for every use-case the provider specific implementation can be found. Implementations for AWS can be located in the `Lambda` subdirectory, implentations for Microsoft Azure in the `Azure` directory and IBM Cloud implementations in the `IBMCloud` directory. With two exceptions: The ToDo API implementations for IBMCloud and AWS Lambda are located in a different repository since these are implemented in Go. Their implementation can be found [here](https://github.com/iaas-splab/faas-migration-go).

Every Implementation has a Readme file describing the steps needed to deploy the use case.

## A note on deployment removal

On AWS all deployments can be removed using the `serverless remove` command that is sometimes wrapped in a makefile. Microsoft Azure and IBM Cloud implementations cannot get deleted using a command. Some IBM implemnetations allow the removal of the IBM Cloud Functions components like actions, APIs and triggers but they do not allow the removal of external services like Object Storage Buckets. these have to be deleted manually. On Azure everything has to be removed manually.

## A general Note on the Tests

The functionality of some deployments can be validated using tests. These tests are written in Go requiring the Go SDK to be installed to run the tests. However, all of these tests do not require any third party libraries. Their functionality is implemented using the Go standard library.

## License

The Source Code is Licensed under Apache License (Version 2.0). See [License](LICENSE) for more informations.
