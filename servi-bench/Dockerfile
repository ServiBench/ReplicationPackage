# Available Python versions: https://hub.docker.com/_/python
ARG PYTHON_VERSION=3.8.12
FROM python:${PYTHON_VERSION}-slim-buster AS build

# Fingerprint source: https://docs.docker.com/engine/install/debian/
# Notice the extra space after the 5th character block
ARG DOCKER_GPG_KEY_FINGERPRINT='9DC8 5822 9FC7 DD38 854A  E2D8 8D81 803C 0EBF CD88'

### Install Docker
# Based on the official installation instructions:
# https://docs.docker.com/engine/install/debian/

RUN apt-get update && apt-get install -y \
  apt-transport-https \
  ca-certificates \
  curl \
  gnupg-agent \
  software-properties-common

# Suppress warning when automatically checking Docker fingerprint:
# https://stackoverflow.com/questions/48162574/how-to-circumvent-apt-key-output-should-not-be-parsed
RUN curl -fsSL https://download.docker.com/linux/debian/gpg | APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add - \
  && APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key fingerprint 0EBFCD88 | grep "$DOCKER_GPG_KEY_FINGERPRINT" \
  && add-apt-repository \
    "deb [arch=$(dpkg --print-architecture)] https://download.docker.com/linux/debian \
    $(lsb_release -cs) \
    stable"
# Yields the following error message that we can ignore: "debconf: delaying package configuration, since apt-utils is not installed"
# See https://stackoverflow.com/questions/51023312/docker-having-issues-installing-apt-utils
RUN apt-get update && apt-get install -y \
  docker-ce-cli \
  make \
  && rm -rf /var/lib/apt/lists/*

# Update pip
RUN /usr/local/bin/python -m pip install --upgrade pip

### Install Python serverless-benchmarker dependencies
COPY setup.py /sb/
WORKDIR /sb
RUN pip install --editable .

### Install serverless-benchmarker code and CLI tool
COPY . /sb
RUN pip install --editable .

### Default command
CMD /usr/local/bin/sb

### Multi-stage build (possible extension)

# Using a multi-stage could reduce the image size but needs more work
# to identify and copy all necessary context required to run sb:
# https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#use-multi-stage-builds
# FROM scratch
# COPY --from=build /sb /sb
# COPY --from=build /usr/local/bin /usr/local/bin
# ENTRYPOINT ["/usr/local/bin/sb"]
# CMD ["--help"]
