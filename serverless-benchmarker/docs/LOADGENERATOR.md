# Load Generator

## AWS Setup

These instructions guide how to setup sb on an EC2 instance.

1. Import or create a new key pair: https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#KeyPairs:
2. Launch a new EC2 instance: https://console.aws.amazon.com/ec2/v2/home?region=us-east-1#LaunchInstanceWizard:
    1. Choose 64-bit x86 AMI: `Amazon Linux 2 AMI (HVM) - Kernel 5.10, SSD Volume Type - ami-0ed9277fb7eb570c9 (64-bit x86) / ami-0a1eddae0b7f0a79f (64-bit Arm)` (2021-12-07)
    2. Choose Instance Type: `t3a.large` ($0.075200 hourly, 2021-12-07). Check [EC2Instances.info](https://instances.vantage.sh/) for alternatives.
    3. Configure Instance: Leave default options
    4. Add Storage: `100GiB General Purpose SSD (gp3)` with default settings `3000 IOPS and 125 MB/s Throughput` (adjust size according to your needs)
    5. Add Tags: `sb => load-generator` (optional)
    6. Configure Security Group: `Create a new security group` with SSH access
    7. Review: `Launch`
    8. Select and existing key pair or create a new key pair: `Choose an existing key pair` and select the key pair created in step 1, then `Launch Instances`
3. `View Instances` and copy `Public IPv4 DNS`
4. SSH into the instance using `ssh -i ~/.ssh/id_rsa ec2-user@PUBLIC_IPV4_DNS`
    1. Optional: Add an alias config to `vim ~/.ssh/config` for example this enables `ssh lg7` (required for SSH agent forwarding):

        ```none
        Host lg7
            HostName ec2-12-34-567-8.compute-1.amazonaws.com
            ForwardAgent yes
            User ec2-user
            IdentityFile ~/.ssh/id_rsa
            IdentitiesOnly yes
        ```

    2. Optional: Use VSCode remotely via `Remote-SSH: Connect to Host...`

5. Update instance and install dependencies:

    ```sh
    sudo yum update -y
    sudo yum install python37 -y
    sudo yum install git tmux htop -y

    # Docker
    sudo amazon-linux-extras install docker -y
    sudo usermod -a -G docker ec2-user
    sudo systemctl enable docker
    sudo service docker start
    ```

6. Clone the application repositories

7. Install the `sb` tool:

    a) [pipx](https://packaging.python.org/guides/installing-stand-alone-command-line-tools/) (recommended for CLI)

    ```bash
    python3 -m pip install --upgrade pip
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath  # might require terminal restart
    cd serverless-benchmarker
    pipx install --editable .
    ```

    b) [venv](https://docs.python.org/3/library/venv.html) (required for SDK when using the programmatic API)

    ```bash
    python3 -m venv sb-env
    source sb-env/bin/activate  # depends on shell
    cd serverless-benchmarker
    python3 -m pip install --upgrade pip
    pip install --editable .
    ```

8. Initialize sb (Note: re-login into instance might be required for picking up venv and Docker ENV)

    ```sh
    sb init
    sb login aws
    ```

## Troubleshooting

* Problem: Dependency conflict between the PyPi packages `packaging` and `pyparsing`: with the error:
  * Error: `ERROR: packaging 21.2 has requirement pyparsing<3,>=2.0.2, but you'll have pyparsing 3.0.6 which is incompatible.`
  * Solution: Upgrade pip `python3 -m pip install --upgrade pip`
  * Workaround: Install compatible version as suggested in this [post](https://stackoverflow.com/questions/69936420/google-cloud-platform-app-deploy-failure-due-to-pyparsing) `pip install 'pyparsing==2.4.7'`
