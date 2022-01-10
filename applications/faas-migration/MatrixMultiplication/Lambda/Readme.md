# MatrixMultiplication - AWS Implementation

This directory contains the AWS specific implementation of the MatrixMultiplication use-case.

## Prerequisites

Apart form the regular prerequisites, this deployment script also needs the [`yq` Utility](https://github.com/mikefarah/yq). `yq` allows querying of YAML documents in a simmilar way to `jq`. It also supports the convertion of YAML documents to JSON.

While `yq` is recommended it is not required since it is only used to get the name of the bucket during deletion.

## Deploying

Before deploying you might want to change the name of the caching bucket in the `serverless.yml`:

```yaml
custom:
  data_bucket_name: cmueller-mtrxmul-data
```

To deploy and build just run:

```bash
make deploy
```

This command can also be used to update the deployment.

## Destroying

To remove the deployment the `make destroy` command can be used. If you do not want to install `yq` you can also run `serverless remove -v` instead. If the removal fails because the bucket is not empty, which happens if calculations do not get executed sucessfuly run `aws s3 rm s3://<Bucket Name> --recursive` to delete the contents of the bucket before retrying the `serverless remove` command

*Note*: Since the step functions plugin for the serverless framework comes with a sample application written in the Dotnet runtime. The `dotnet lambda package` command used to compile the function will fail. A quick fix for this is the removal of the `node_modules` folder. Because of this problem we remove the `node_modules` folder before building and rerun `npm install` afterwards. As a result, it is possible that the `make destroy` or `serverless remove` commands might fail due to a missing plugin. This especially happens if the `make deploy` command has been interrupted manually. To fix this just run `npm install` manually.

## Invoking and testing

The invokation and testing procedures for the AWS implementation is described in the general matrix multiplication [Readme](../Readme.md).
