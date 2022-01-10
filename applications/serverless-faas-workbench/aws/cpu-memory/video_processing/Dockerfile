FROM lambci/lambda:build-python3.8

# opencv dependencies: source: https://github.com/NVIDIA/nvidia-docker/issues/864#issuecomment-452023152
RUN yum -y install libXext libSM libXrender

ARG SERVERLESS_VERSION=2.64.1
ENV SERVERLESS_VERSION $SERVERLESS_VERSION

# Supported Nodejs distributions for Amazon Linux
# https://github.com/nodesource/distributions#installation-instructions-1
RUN curl -fsSL https://rpm.nodesource.com/setup_12.x | bash - \
    && yum -y install nodejs \
    && yum -y install gcc-c++ make \
    && curl -sL https://dl.yarnpkg.com/rpm/yarn.repo | tee /etc/yum.repos.d/yarn.repo \
    && yum -y install yarn

# Install the serverless framework globally
RUN yarn global add serverless@$SERVERLESS_VERSION