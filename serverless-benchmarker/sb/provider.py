import os
import logging
import subprocess


class Provider:
    SUPPORTED = ['aws', 'azure', 'google', 'ibm', 'pulumi']
    MOUNT_DIRS = {
        'aws': '/root/.aws',
        'azure': '/root/.azure',
        'google': '/root/.config/gcloud',
        'ibm': '/root/.bluemix',
        'pulumi': '/root/.pulumi'
    }
    LOGIN_CMDS = {
        'aws': 'aws configure',
        'azure': 'az login',
        'google': 'gcloud init',
        'ibm': 'ibmcloud login',
        'pulumi': 'login'
    }
    CHECK_CREDENTIALS_CMDS = {
        'aws': 'aws sts get-caller-identity',
        'azure': 'az account show',
        'google': 'gcloud auth',
        'ibm': 'ibmcloud regions',
        'pulumi': 'pulumi whoami'
    }
    CLI_IMAGES = {
        # Docs and Tags: https://hub.docker.com/r/mikesir87/aws-cli
        'aws': 'mikesir87/aws-cli:1.18.188',
        # Docs: https://hub.docker.com/_/microsoft-azure-cli
        # Tags: https://mcr.microsoft.com/v2/azure-cli/tags/list
        'azure': 'mcr.microsoft.com/azure-cli:2.9.1',
        # Docs and Tags: https://hub.docker.com/r/google/cloud-sdk
        'google': 'google/cloud-sdk:315.0.0-alpine',
        # Tags: https://hub.docker.com/r/ibmcom/ibm-cloud-developer-tools-amd64/tags
        'ibm': 'ibmcom/ibm-cloud-developer-tools-amd64:1.2.3',
        # Docs and Tags: https://hub.docker.com/r/rubenfunai/aliyun-cli
        'alibaba': 'rubenfunai/aliyun-cli:3.0.60-amd64',
        # Docs and Tags: https://hub.docker.com/r/pulumi/pulumi/tags?page=1&ordering=last_updated
        # Slimmer image alternatives: https://www.pulumi.com/blog/introducing-new-docker-images/
        'pulumi': 'pulumi/pulumi:v2.21.2'
    }

    def __init__(self, name) -> None:
        if name in Provider.SUPPORTED:
            self.name = name
        else:
            raise ValueError(f"Unsupported provider {name}. Supported: {Provider.SUPPORTED}")

    def check_credentials(self):
        # Also see tests/integration/credentials_test.py and fixtures/credentials/*
        cmd = f"docker run --rm -it -v {self.volume_mount()} {self.cli_image()} {self.check_credentials_cmd()}"  # noqa: E501
        logging.info(cmd)
        os.system(cmd)

    def login(self, prompt=False):
        cmd = f"docker run --rm -it -v {self.volume_mount()} {self.cli_image()} {self.login_cmd()}"
        # Workaround for reading entire AWS credentials file
        if self.name == 'aws' and prompt:
            cmd = f"docker run --rm -it -v {self.volume_mount()} {self.cli_image()} /bin/sh -c 'cat > /root/.aws/credentials'"  # noqa: E501
            print('Paste a ~/.aws/credentials file with a [default] profile, press enter, and save it via Ctrl-D or Ctrl-Z (Windows).')  # noqa: E501
        logging.info(cmd)
        os.system(cmd)

    def logout(self):
        cmd = f"docker volume rm {self.volume_name()}"
        proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if(proc.returncode == 0):
            logging.info(f"Removed all {self.name} credentials.")
        elif(proc.stderr.startswith('Error: No such volume:')):
            logging.info(f"No credentials for {self.name} present.")
        else:
            logging.warning(f"Failed to remove {self.name} credentials.")

    def volume_mount(self) -> str:
        return f"{self.volume_name()}:{self.mount_dir()}"

    def volume_name(self) -> str:
        return f"{self.name}-secrets"

    def mount_dir(self) -> str:
        return Provider.MOUNT_DIRS[self.name]

    def login_cmd(self) -> str:
        return Provider.LOGIN_CMDS[self.name]

    def check_credentials_cmd(self) -> str:
        return Provider.CHECK_CREDENTIALS_CMDS[self.name]

    def cli_image(self) -> str:
        return Provider.CLI_IMAGES[self.name]
