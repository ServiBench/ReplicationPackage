# Thumbnail Generator - Azure Implementation

This is the Azure implementation of the Thumbnail Generator use-case. Apart form the regular dependencies on Azure this implementation also needs a JDK (version 8) and Apache Maven to be compiled.

## Configuring the deployment

Before deploying you might want to change the name of the resulting function app, the used resouce group and the region. This is done by changing the variable values in the `Makefile`

```Makefile
# Configuration
RESOURCE_GROUP := faas-migration
FUNCTION_APP_NAME := cmueller-bt-thumbnail-generator
REGION := westeurope
```

## Deploying

To deploy the application run the following command in this directory:

```bash
make deploy
```

This will compile the functon. This command will also create resources if they do not exist. For example it will create a StorageAccount instance with a "random looking" name that is used for storing the images and the functions payload. It will also create the `input` and `output` containers used to store the images and thumbnails.

This command is also used to update the deployment.

## Running locally

Unlike other implementations local execution only works after the application has been deployed. Thats because of the storage account created by maven. To locally run the functions after the deployment has finished just run

```bash
make run_local
```

## Testing

### Uploading an Image using the Upload Function

To upload a image using the `Upload-Image` Function it must be encoded as Base64, just like the AWS implementation. To upload an image the following curl command can be used

```bash
cat <FileName> | base64 -w0 | curl -v -d @- "https://<FunctionApp Name>.azurewebsites.net/api/Upload-Image?name=<FileNameInBlobStorage>"
```

To test the functionality of the use-case we are providing some PNG files containing two images ([See test-images](../test-images)). The folder also contains the expected result for both files.

### Verifying the contents

The contents of the containers can be verified by viewing them on the Web Interface this also allows you to download the files.

If you just want to see if the files have been processed you can run `make ls_input` or `make ls_output` to list the contents of the corresponding container in a very simplistic and human readable json format.

An example output of `make ls_output`

```json
{
  "file_name": "test.jpg",
  "file_size": 8029,
  "creation_timestamp": "2019-08-20T22:27:20+00:00"
}
{
  "file_name": "test1.jpg",
  "file_size": 8029,
  "creation_timestamp": "2019-08-20T22:27:20+00:00"
}
{
  "file_name": "test2.jpg",
  "file_size": 8029,
  "creation_timestamp": "2019-08-20T22:27:20+00:00"
}
```
