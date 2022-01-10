# Development

Describes the development setup, implementation insights, challenges, etc.

## Install dependencies

```sh
make install
```

## Linting

```sh
make lint
```

## Tests

```sh
make test
# Selectively run unit or integration tests
make unit_test
make integration_test
```

## VSCode

* Example settings: [settings.sample.json](../.vscode/settings.sample.json). Change `python.pythonPath`
* Recommended plugins: [extensions.json](../.vscode/extensions.json)
* [Python testing in VSCode](https://code.visualstudio.com/docs/python/testing)

## Debugging

* Use the tests and local mode to debug
* Alternatively, an interactive Python shell can be used as breakpoint by inserting the following snippet into the code:

  ```py
  # Native
  import code; code.interact(local=dict(globals(), **locals()))
  # With ipdb (requires dev dependencies or pip install ipdb)
  import ipdb; ipdb.set_trace()
  ```

## Useful Python Tools

* [pip-check](https://pypi.org/project/pip-check/) gives you a quick overview of all installed packages and their update status.
* [pipdeptree](https://pypi.org/project/pipdeptree/) is a command line utility for displaying the installed python packages in form of a dependency tree.

## Design

* [DESIGN_V1](./DESIGN_V1.md)

## Troubleshooting

### lzma module missing

```none
packages/pandas/compat/__init__.py:124: UserWarning: Could not import the lzma module. Your installed Python is incomplete. Attempting to use lzma compression will result in a RuntimeError.
  warnings.warn(msg)
```

Some native dependencies are missing for a complete installation. See [this StackOverflow post](https://stackoverflow.com/a/58518449):

1. `brew install xz`
2. Reinstall Python `pyenv install 3.10.1`

### M1 ARM Support

The apigw_node app failed with the following error:

```
INFO:root:docker=docker run --rm -v aws-secrets:/root/.aws -v '/Users/anonymous/Projects/Serverless/test-apps-yes/serverless-patterns/apigw-lambda-cdk/src':/apps/src --entrypoint='' node-cdk-apigw-node /bin/sh -c "cd '/apps/src' && cdk bootstrap aws://WARNING: The requested image's platform (linux/amd64) does not match the detected host platform (linux/arm64/v8) and no specific platform was requested
123456789012/eu-north-1"
INFO:run:/bin/sh: 2: Syntax error: Unterminated quoted string
```

We might need to detect the architecture on the host using cross-platform compatible Python and pass it into the Docker context to specify the architecture when running Docker commands. The first step would be to fix the Docker command and then adjust sb accordingly.

# Development Notes for legacy version

* [Sample output](./OUTPUT.md)

## Next Steps

* figure out how to deal with async function triggers (this can be done using the 'Event'
  invocation type in the `boto3` lib - the issue is how to collect the log messages).
* trigger events based on S3 files and dyanmodb updates
* set up a framework for regular gathering of data

## Challenges

* Get aws_uid automatically via boto3: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/iam.html
* There needs to be a way to pass/persist configuration between the phases setup, execute, and cleanup. For example when testing API gateways, the setup phase creates unique IDs and endpoint URLs, which then are required for executing or cleaning up the created infrastructure.
* The metric architecture needs to make units explicit. Our harness should promote best practices handling units (they are important to get right!).

## Insights

* The Serverless Framework introduces considerable overhead for invoking function in comparison to CLI invokation. AWS Lambda `sls invoke` takes ~2.4s vs ~1.2s with the AWS CLI `aws lambda invoke`.

## Function Runtimes

* [AWS runtimes](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html)
* [Google runtimes](https://cloud.google.com/functions/docs/concepts/exec)
* [Azure runtimes](https://docs.microsoft.com/en-us/azure/azure-functions/functions-versions)

* Nodejs: 10.x
  * Currently (2020-02-12), most widely supported runtime although only in Beta for Google

## Requirements (all dependencies for old version)

* Python 3.6+ toolchain and dependencies (for boto3 AWS):
  * `pip install -r requirements.txt`
* Nodejs toolchain and dependencies (for Serverless Framework):
  * `npm install`
* Golang (e.g., 1.13.x) toolchain and dependency:
  * `go get 'github.com/aws/aws-lambda-go/lambda'`
* [AWS account and credentials](https://serverless.com/framework/docs/providers/aws/guide/credentials/)
  * Interactively: `aws configure`
  * `export AWS_ACCESS_KEY_ID=<your-key-here>`
  * `export AWS_SECRET_ACCESS_KEY=<your-secret-key-here>`
* [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv1.html) v1
  * Covered in Python dependencies
* AWS execution role (for hardcoded boto3 part)
  * `cd setup && aws iam create-role --role-name lambda_execution_role --assume-role-policy-document file://lambdaRoleTrustPolicy.json`
* AWS region config via [credentials file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) (for boto3 part)
  * `aws configure set region eu-west-1`
  * `~/.aws/credentials` or `~/.aws/config` should have an entry `region=eu-west-1`
* Set environment variable `AWS_ACCOUNT_UID`
  1. AWS account and logged into CLI `aws configure`
  2. AWS account UID `aws sts get-caller-identity` (i.e., the "Account" field)
  3. `export AWS_ACCOUNT_UID=123456789012`
* [Google account and credentials](https://serverless.com/framework/docs/providers/google/guide/credentials/)
  * Save keyfile to `/tmp/.gcloud/faasbenchmark.json`
  * Project name (check serverless.yml!)
