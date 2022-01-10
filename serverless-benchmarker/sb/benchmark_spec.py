import json
from pathlib import Path, PurePosixPath, PureWindowsPath
from sb.event_log import EventLog
import subprocess
import os
import shutil
import platform
import logging
from subprocess import TimeoutExpired

from sb.provider import Provider
from sb.workload_generator import WorkloadGenerator

logger = logging.getLogger('run')

DEFAULT_TIMEOUT = 30  # seconds


def win_vol(path) -> str:
    r"""Converts a Windows path into a Docker-compatible path
    without a colon. Returns Posix paths unchanged.
    Example: win_vol(PureWindowsPath("C:\Users\anonymous\Projects"))
    => "/C/Users/anonymous/Projects"
    """
    if(isinstance(path, PureWindowsPath)):
        posix_path = PurePosixPath(path)
        path_without_colon = str(posix_path).replace(':\\', '')
        return f"/{path_without_colon}"
    else:
        return path


class BenchmarkSpec:
    DEFAULT_SCRIPT = 'workload_script.js'
    DEFAULT_OPTIONS = 'workload_options.json'
    CHECK_RETURNCODE_DEFAULT = True
    IMAGES = {
        'aws_cli': Provider.CLI_IMAGES['aws'],
        'azure_cli': Provider.CLI_IMAGES['azure'],
        'google_cli': Provider.CLI_IMAGES['google'],
        'ibm_cli': Provider.CLI_IMAGES['ibm'],
        'alibaba_cli': Provider.CLI_IMAGES['alibaba'],
        'pulumi_cli': Provider.CLI_IMAGES['pulumi'],
        # Docs and Tags: https://hub.docker.com/r/amaysim/serverless
        'serverless_cli': 'amaysim/serverless:2.64.1',
        # Language runtime names inspired by AWS docs:
        # https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html
        # Docs and Tags: https://hub.docker.com/_/node/?tab=description
        'node12.x': 'node:12.22.7',
        # Docs and Tags: https://hub.docker.com/_/python
        'python3.8': 'python:3.8.8',
        'python3.9': 'python:3.9.9',
        # Docs and Tags: https://hub.docker.com/_/golang
        'go1.x': 'golang:1.16.0',
        # Docs: https://hub.docker.com/_/openjdk?tab=description
        # Tags:
        # https://github.com/docker-library/docs/blob/master/openjdk/README.md#supported-tags-and-respective-dockerfile-links
        'java8': 'openjdk:8',
        # Docs and Tags: https://hub.docker.com/_/microsoft-dotnet-sdk
        'dotnetcore3.1': 'mcr.microsoft.com/dotnet/sdk:3.1',
        # Docs and Tags: https://hub.docker.com/r/loadimpact/k6
        'k6': 'loadimpact/k6:0.34.1'
    }

    def __init__(self, config, name=None):
        self.config = config
        # The first top-level key defines the benchmark name by convention
        self.name = name or list(config.keys())[0]
        self.event_log = EventLog(self)
        # Indicates whether the last `spec.run` command succeeded
        # Used to implement conditional `.sb` cleanup
        self.last_run_success = True

    def run_k6(self, envs={}, options='', image='k6'):
        """Runs k6 with automated workload injection and csv logging.
        A 'workload_script.js' is expected in the same directory as the
        *_benchmark.py file. Alternative locations are configurable via
        'workload_script' and 'workload_options.json'.
        Attr:
        envs: dict of environment variables
        options: optional k6 command line options https://k6.io/docs/using-k6/options
        image: the Docker image with k6 installation
        """
        workload_script, workload_options = self.workload_file_paths()
        cmd = (
            "k6 run"
            f"{self.key_value_args(envs, '--env')}"
            f' --config "{workload_options}"'
            f" --out csv={self.workload_log_file()}"
            f" {options}"
            f" {workload_script}"
        )
        self.run(cmd, image=image)

    def key_value_args(self, arg_dict, flag) -> str:
        """Converts a dict into key=value cli arguments with a flag.
        Example: '--env "key1=value1" --env "key2=value2"'
        """
        envs_arg = ''
        for key, value in arg_dict.items():
            escaped_value = str(value).replace("'", "\\'")
            envs_arg += f" {flag} '{key}={escaped_value}'"
        return envs_arg

    def run(self, cmd, image='alpine:3.12.0',
            shell='/bin/sh', check=None) -> str:
        """Runs a given `cmd` in a Docker `image` and returns its stdout.
        Mounts the root directory into the container as well as provider
        secrets if a provider is specified in the BENCHMARK_CONFIG.
        image: supports global aliases as defined in IMAGES.
        Examples:
        * spec.run('pwd', image='alpine:3')
        * spec.run('sls deploy', image='serverless_cli')
        Optional arguments:
        * shell: specifies the login shell wherein the `cmd` executes.
        * check: fails upon non-zero exit status if set to True.
                 Defaults: True during prepare phase and False during cleanup.
        """
        # Resolve image aliases
        if(image in BenchmarkSpec.IMAGES.keys()):
            image = self.image(image)
        # Set status code check default
        if(check is None):
            check = BenchmarkSpec.CHECK_RETURNCODE_DEFAULT
        # Escape double quotes for shell
        escaped_cmd = cmd.replace('"', '\\"')
        # Escape dollar sign ($) for local mode support on Windows
        if(platform.system() != 'Windows'):
            escaped_cmd = escaped_cmd.replace('$', r'\$')
        docker_cmd = (
            "docker run --rm"
            f"{self.secrets_mount()}"
            f" -v '{win_vol(self.host_root_path())}':{self.mount_dir()}"
            f"{self.user_permissions()}"
            f" --entrypoint=''"  # Some containers already have ENTRYPOINTS, remove them
            f" {image} {shell} -c \"cd '{self.bench_dir()}' && {escaped_cmd}\""
        )
        # MAYBE: provide option to execute in full local mode too.
        # Need to make the local flag somehow accessible.
        # if mode.local:
        #     cmd = escaped_cmd
        logging.info(f"docker={docker_cmd}")
        # See: https://docs.python.org/3/library/subprocess.html#subprocess.Popen.stderr
        proc = subprocess.Popen(docker_cmd, shell=True, text=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        log = []
        pulling = False
        for line in iter(proc.stdout.readline, ''):
            logger.info(line.rstrip())
            # Filter out Docker image pull log if image is unavailable
            # Pulling begins
            if line.startswith('Unable to find image'):
                pulling = True
            # Pulling ends
            elif pulling and line.startswith('Status: Downloaded newer image'):
                pulling = False
            # Only capture non-pulling lines
            elif not pulling:
                log.append(line)

        # Need to use communicate to wait for subprocess completion as described here:
        # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.communicate
        # Warning: MUST use communicate if stderr is PIPE. See:
        # https://docs.python.org/3/library/subprocess.html#subprocess.Popen.stderr
        try:
            _, errs = proc.communicate(DEFAULT_TIMEOUT)
            # Update status flag of last run command
            if proc.returncode == 0:
                self.last_run_success = True
            else:
                self.last_run_success = False
            if(check and proc.returncode != 0):
                err_msg = (
                    f"The spec.run() command `{cmd}` exited unsuccessfully."
                    f" Full Docker command:\n{docker_cmd}"
                )
                raise Exception(err_msg)
        except TimeoutExpired:
            logging.warning(f"Killing process after waiting for {DEFAULT_TIMEOUT}s ...")
            proc.kill()
            _, errs = proc.communicate()
            logging.warning(errs)

        return ''.join(log)

    def shell(self, image, shell='/bin/bash'):
        """Starts an interactive `shell` in a Docker `image`
        with the same auto-mounting as spec.run()."""
        # Resolve image aliases
        if(image in BenchmarkSpec.IMAGES.keys()):
            image = self.image(image)
        docker_cmd = (
            "docker run --rm -it"
            f"{self.secrets_mount()}"
            f" -v '{win_vol(self.host_root_path())}':{self.mount_dir()}"
            f"{self.user_permissions()}"
            f" --entrypoint=''"  # Some containers already have ENTRYPOINTS, remove them
            f" {image} {shell} -c \"cd '{self.bench_dir()}' && {shell}\""
        )
        logging.info(f"docker={docker_cmd}")
        os.system(docker_cmd)

    def mount_dir(self):
        """Returns the root mount path for apps within containers."""
        return f"/apps/{self.host_root_path().name}"

    def bench_dir(self):
        """Returns the full path (including sub-path) where the benchmark
        file resides (i.e., benchmark working directory)"""
        return f"/apps/{self.sub_path()}"

    def build(self, image_tag, file='Dockerfile'):
        """Builds a Dockerfile and tags it with `image_tag`."""
        logging.info(f"Building {file} for tag {image_tag} ...")
        build_cmd = f"docker build -f {file} . --tag {image_tag}"
        status = os.system(build_cmd)
        if status != 0:
            err_msg = (
                f"Error during building `{file}`."
                f" Full Docker command:\n{build_cmd}"
            )
            raise Exception(err_msg)

    def secrets_mount(self):
        """Returns the Docker mount config if a provider is specified
        or an empty string otherwise.
        Starts with a whitespace if present."""
        try:
            provider = self['provider']
            # Hack for Pulumi: provider can be a list to
            # support mounting multiple credentials
            if isinstance(provider, list):
                secrets_mount = ''
                for p in provider:
                    vol_mnt = Provider(p).volume_mount()
                    secrets_mount += f" -v {vol_mnt}"
                return secrets_mount
            else:
                vol_mnt = Provider(provider).volume_mount()
                secrets_mount = f" -v {vol_mnt}"
                return secrets_mount
        except (KeyError, ValueError):
            logging.info('Invalid or unspecified provider. No credentials are injected.')
            return ''

    def user_permissions(self):
        if(self.host_system() == 'Linux'):
            # Need to run container as root until docker supports non-root volumes:
            # https://github.com/moby/moby/issues/2259
            return ' -u root'
            # Alternatively use proper permissions from host:
            # user_group = self.host_user_group()
            # return f" -u {user_group}"
        else:
            return ''

    def host_user_group(self):
        if 'host_user_group' in self.config['sb']:
            return self.config['sb']['host_user_group']
        else:
            logging.warning('No host user group config. Using dynamic detection.')
            # TODO: impl. fallback
            # return Benchmark.host_user_group()
            return None

    def sub_path(self):
        """Returns the relative path to the benchmark directory (i.e., where the
        *_benchmark.py file resides) underneath the root path.
        Example:
        * str(self.host_root_path()) == '/apps/higher_root_path'
        * str(self.host_path()) ==
            '/Users/anonymous/Projects/Serverless/serverless-benchmarker/tests/fixtures/higher_root_path/azure'
        * self['root'] == '..'
        => str(self.sub_path()) == 'higher_root_path/azure'
        """
        rel_path = self.host_path().relative_to(self.host_root_path())
        # NOTE: would need to conditionally use PureWindowsPath for supporting local mode on Windows
        return PurePosixPath(self.host_root_path().name).joinpath(rel_path)

    def host_root_path(self):
        """Returns the root benchmark path on the Docker host enclosing all resources.
        This path adjusts for potential higher root path configurations of the benchmark
        as resources might be shared at higher-level directories between similar benchmarks.
        """
        res = self.host_path()
        for _ in range(self.root_levels_up()):
            res = res.parent
        return res

    def root_levels_up(self):
        """Returns the number of levels the root path goes up"""
        if self['root']:
            return len(self['root'].split('/'))
        else:
            return 0

    def host_path(self):
        """Returns the pure path to the benchmark directory on the calling host"""
        if self.host_system() == 'Windows':
            return PureWindowsPath(self.config['sb']['host_path'])
        else:
            return PurePosixPath(self.config['sb']['host_path'])

    def host_system(self) -> str:
        return self.config['sb']['host_system']

    def logs_directory(self) -> Path:
        """Returns a relative Python Path to the logs directory.
        Typically next to the *_benchmark.py file.
        """
        start = self.event_log.last_event_time('invoke', 'start')
        if start is None:
            return None
        timestamp = start.strftime('%Y-%m-%d_%H-%M-%S')
        dirpath = Path(f"logs/{timestamp}")
        dirpath.mkdir(parents=True, exist_ok=True)
        return dirpath

    def workload_log_file(self):
        return self.logs_directory() / 'k6_metrics.csv'

    def workload_options(self) -> dict:
        """Returns a k6 options dictionary."""
        gen = WorkloadGenerator(self['workload_type'],
                                self['scale_factor'], self['scale_type'],
                                self['workload_trace'],
                                self['seconds_to_skip'])
        return gen.generate_trace()

    def create_workload_options_file(self, path, workload_options=None):
        script, options = self.workload_file_paths()
        options_path = Path(path) / options
        logger.info(f"Creating k6 options: {options_path}")
        k6_config = None
        # passed options dict takes precedence
        if isinstance(workload_options, dict):
            k6_config = workload_options
        # copy json config file directly if provided
        elif workload_options and BenchmarkSpec.is_existing_json_file(workload_options):
            shutil.copyfile(workload_options, options_path)
            # return because we already created the file through copying
            return
        else:
            # generate via workload generator
            k6_config = self.workload_options()

        # write k6 config to workload_options.json file
        with open(options_path, 'w') as options_file:
            json.dump(k6_config, options_file)

    def is_existing_json_file(path) -> bool:
        p = Path(path)
        return p.suffix == '.json' and p.is_file()

    def workload_file_paths(self):
        script = self['workload_script']
        options = self['workload_options']
        # Use defaults for unspecified configs
        if script is None and options is None:
            script = BenchmarkSpec.DEFAULT_SCRIPT
            options = BenchmarkSpec.DEFAULT_OPTIONS
        # Only use default for unspecified script
        elif script is None:
            script = BenchmarkSpec.DEFAULT_SCRIPT
        # Use same directory as script for options assuming that
        # we usually want the options file right next to the script file
        elif options is None:
            script_path = Path(script)
            options_path = script_path.parent / BenchmarkSpec.DEFAULT_OPTIONS
            options = str(options_path)
        # else: use specified config assigned above
        return script, options

    # Forward square bracket getter and setter to config dictionary namespaced by benchmark name
    def __getitem__(self, key):
        """Return the item in the benchmark spec with key `key` or None.
        Raises a KeyError if the benchmark has no default config for its name.
        """
        return self.config[self.name].get(key)

    def __setitem__(self, key, value):
        """Set the value `value` for the key `key`.
        Raises a KeyError if the benchmark has no default config for its name.
        """
        self.config[self.name][key] = value

    def pop(self, key, default):
        """Deletes the key `key` and returns its value if present or `default` otherwise.
        Raises a KeyError if the benchmark has no default config for its name.
        """
        return self.config[self.name].pop(key, default)

    def image(self, name) -> str:
        """Returns the Docker image for a given name key.
        Raises a KeyError if the name key is not supported.
        """
        return BenchmarkSpec.IMAGES[name]
