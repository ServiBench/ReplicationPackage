# MatrixMultiplication - Azure

## Building and Deploying

To Deploy please follow the generic [Azure Deployment Guide](/azure_deploy.md)

## Starting a Multiplication

A Multiplication can be Launched by firing a get Request on the following Endpoint: http://<APPNAME>/api/TriggerMatrixMultiplication

Where `<APPNAME>` represents the link to the function app or to the locally running function host (Usually: `http://127.0.0.1:7071`)

It supports the Following Query Parameters:

- `size`: The size of the matrices to generate
- `seed`: The seed for the Random number generator
- `max`: The maximum value a entry in the input matrices should have (from 0 to max, has to be positive)
- `callback`: placing a URL here will cause the CreateReport function to send a HTTP POST request to the set URL with thre rport attached as JSON body.

All these parameters are optional and can be ommited. If so defaults are used!

More details on how the workflow is invoked can be found in the General matrix multiplication [Readme](../Readme.md).
