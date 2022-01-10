# https://hub.docker.com/_/node
# CDK recommends using an active LTS version of nodejs: https://github.com/aws/aws-cdk
FROM node:16

# https://www.npmjs.com/package/aws-cdk
# specific version or latest
# NOTE: potential build failure when this version gets out of sync with the package.json
# Workaround: Need to update here or pin versions using package-lock.json
ARG AWS_CDK_VERSION=latest
ENV AWS_CDK_VERSION $AWS_CDK_VERSION

# Install AWS CDK globally
RUN npm install -g aws-cdk@${AWS_CDK_VERSION}

# Install global app dependencies
RUN npm install -g typescript && npm install -g ts-node
