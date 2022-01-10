# Amazon Web Services (aws)

* [AWS Console](https://console.aws.amazon.com/)

## Setup

1. Sign up for an AWS account: https://aws.amazon.com/free
2. Open the `Users` page under Identity & Access Management (IAM): https://console.aws.amazon.com/iam/home#/users
3. Click on `Add user`, enter a username (e.g., `sb-admin`), and enable `Programmatic access`.
4. On the next page, choose `Attach existing policies directly` and enable `AdministratorAccess`.
5. Confirm everything by clicking `Create user`
6. Copy the `Access key ID` and  `Secret access key` to a safe place.
7. Run `sb login aws` and enter your access and secret key to authenticate.

For more detailed instructions, checkout the credentials documentation of the [Serverless Framework](https://www.serverless.com/framework/docs/providers/aws/guide/credentials/).

## Advanced Configuration

Run `sb login aws --prompt` to provide a custom [AWS credentials file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) (i.e., `~/.aws/credentials`) with a `[default]` profile.
This enables support for SSO-based authentication, for example through [onelogin-python-aws-assume-role](https://github.com/onelogin/onelogin-python-aws-assume-role).
