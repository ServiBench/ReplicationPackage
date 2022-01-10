import pkg_resources
import logging
import platform
from pathlib import Path
import sys
import os
import time
import fire

from sb.cli.config_cmd import ConfigCmd
from sb.benchmark import Benchmark
from sb.benchmark_spec import BenchmarkSpec, win_vol
from sb.provider import Provider
from sb.aws_trace_analyzer import AwsTraceAnalyzer
from sb.aws_trace_downloader import AwsTraceDownloader
from sb.azure_trace_downloader import AzureTraceDownloader
import sb.aws_trace_migrator as aws_trace_migrator


SB_IMAGE = 'serverless-benchmarker'
WAIT_AFTER_PREPARE = 0  # seconds


def main():
    """sb.sb entry point"""
    # Default config for non-member methods (e.g., login and logout)
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    fire.Fire(Sb)


class Sb:
    """Serverless Benchmarker (sb) API class that is automatically exposed as
    CLI using Python Fire (https://github.com/google/python-fire).
    """

    @staticmethod
    def version():
        """Retrieve version from setup.py"""
        return pkg_resources.require('serverless-benchmarker')[0].version

    @staticmethod
    def login(provider, prompt=False):
        """Login to cloud providers.
        --prompt: flag to enable advanced credentials configuration."""
        Provider(provider).login(prompt)

    @staticmethod
    def check_credentials(provider):
        """Checks if the credentials work for a given provider."""
        Provider(provider).check_credentials()

    @staticmethod
    def logout(provider):
        """Remove cloud provider credentials by deleting the secrets-* docker volume."""
        Provider(provider).logout()

    @staticmethod
    def init():
        """Build the serverless-benchmarker (sb) docker image."""
        os.system(f"docker build -t {SB_IMAGE} {Sb.sb_root()}")

    @staticmethod
    def sb_root() -> Path:
        """Return the root directory of the sb tool."""
        return Path(__file__).parent.parent.absolute()

    @staticmethod
    def migrate_traces(log_path, replace=False):
        """Migrates traces from old single-line format to new one trace-per-line format."""
        aws_trace_migrator.migrate_traces(log_path, replace)

    @staticmethod
    def detect_file(file):
        """Returns a detected *_benchmark.py file or None otherwise."""
        if Path(file).is_file():
            return file
        file_matches = Path().glob(file)
        files = list(file_matches)
        if len(files) == 1:
            return files[0]
        elif len(files) == 0:
            logging.debug('Failed to detect a `*_benchmark.py` file in the current directory. \
Change directory or explicitly specify a file using `--file=FILE|pattern`.')
            return None
        else:
            logging.debug('Detected multiple `*_benchmark.py` files in the current directory. \
Explicitly specify a unique file using `--file=FILE|pattern`.')
            return None

    @staticmethod
    def key_value_args(arg_dict) -> str:
        """Converts a dict into key=value cli arguments.
        Example: --key1=value1 --key2=value2
        """
        args = ''
        for key, value in arg_dict.items():
            escaped_value = str(value).replace("'", "\\'")
            args += f" --{key}={escaped_value}"
        return args

    # TODO: change debug to False by default after major dev phase
    # because we want to avoid Python version incompatibilities as the
    # local code is directly linked into the container (which might run another Python version).
    # To keep development easy, we want to avoid re-building the container after each change.
    def __init__(self, file='*_benchmark.py', local=False, debug=True,
                 log_level='INFO', docker=False):
        """Inits the Serverless Benchmarker CLI API.

        Args:
            file: Path or pattern to a benchmark file.
            local: Flag to enable the local execution mode where everything runs locally
                instead within Docker. Requires local dependency and credentials configuration.
            debug: Flag to enable debug mode, which auto-mounts sb code into Docker (avoids
                rebuild of the sb container after code changes) and runs in interactive mode.
            log_level: Python log level: https://docs.python.org/3/library/logging.html#levels
            docker: Flag to enable experimental docker mode, which runs sb itself within Docker.
                Important: Unsupported on Linux host (might only work with root user).
        """
        level = logging.getLevelName(log_level)
        logging.basicConfig(stream=sys.stdout, level=level)
        self.initialize(file)
        # Python Fire command groups:
        # https://github.com/google/python-fire/blob/master/docs/guide.md#grouping-commands
        # Only available when properly initialized
        if self.bench:
            self.config = ConfigCmd(self.bench)
        # Flags
        self.local = local
        self.debug = debug
        self.log_level = log_level
        self.docker = docker

    def initialize(self, file):
        """Detects and bootstraps the sb benchmark with its configuration (i.e., benchmark spec)"""
        bench_file = Sb.detect_file(file)
        if bench_file is not None:
            self.bench = Benchmark.initialize(bench_file)
        else:
            self.bench = None

    def __str__(self):
        """Return empty string to avoid interactive prompt upon returning self."""
        return ''

    def check_bench_init(self):
        """Raises an error if bench is not initialized (i.e., missing benchmark file)"""
        if self.bench is None:
            raise ValueError("Failed to find a single unique benchmark file. \
Use --log_level=DEBUG to get more details.")

    def name(self) -> str:
        """Returns the name of the benchmark.
        NOTE: cannot be chained"""
        self.check_bench_init()
        return self.bench.name

    def status(self):
        """Shows the last event and total duration."""
        self.check_bench_init()
        event_log = self.bench.spec.event_log
        logging.info(self.bench.name)
        logging.info(f"last_event={event_log.last_event()}")
        logging.info(f"total_duration={event_log.total_duration()}")
        return self

    def wait(self, seconds):
        """Waits idle for a given number of `seconds`.
        Useful for command chaning. For example:
        sb invoke 10 wait 90 get_traces"""
        logging.info(f"Waiting for {seconds} seconds ...")
        time.sleep(seconds)
        return self

    def test(self):
        """Runs prepare, invoke, and cleanup workflow."""
        self.check_bench_init()
        if self.docker:
            self.run_in_docker('test', restore_config=False)
        else:
            self.bench.chdir()
            self.bench.prepare()
            if WAIT_AFTER_PREPARE > 0:
                logging.info(f"Waiting {WAIT_AFTER_PREPARE} seconds before invoking ...")
                time.sleep(WAIT_AFTER_PREPARE)
            self.bench.invoke(workload_type=3)
            self.bench.cleanup()
        return self

    def prepare(self):
        """Deploys a benchmark in a cloud environment."""
        self.check_bench_init()
        if(self.docker):
            self.run_in_docker('prepare')
        else:
            self.bench.chdir()
            self.bench.prepare()
        return self

    def invoke(self, workload_type=None, **kwargs):
        """
        Invokes a benchmark with a given workload type.
        Examples:
          sb invoke 10 (using 10 sequential iterations)
          sb invoke spikes --scale_factor=2 --scale_type=compound
          sb invoke custom --workload_options=my_k6_config.json

        Main argument:
          workload_type: Defines the invocation pattern for a benchmark.
                         * default: single
                         * supported patterns: steady|bursty|spikes|jump
                         * numeric value for sequential iterations: e.g., 10
                         * custom: when providing a custom workload_trace CSV
                                   or a custom k6 workload_options JSON
        Optional arguments:
          scale_factor=1: the multiplication factor for scaling a workload
          scale_type=linear: the scaling method: linear|compound
          workload_options=None: path to a k6 config JSON or a dictionary of k6 options.
                                 See k6 options docs: https://k6.io/docs/using-k6/options/
          workload_trace=None: path to a CSV file with per minute invocation rates.
                               Format: single column called "InvocationsPerMinute".
                               Examples: see data/workload_traces.
          seconds_to_skip=3 * 60: number of seconds of a workload trace that are skipped to
                                  alleviate the bootstrapping issue of 0 rps at t=0 seconds.
        """
        self.check_bench_init()
        if(self.docker):
            # NOTE: an extension for custom CSV workload traces or custom JSON workload options
            # would need to adjust relative paths within Docker or add an addition mount to ensure
            # a given file is available in the container context.
            self.run_in_docker(f"invoke {workload_type} {Sb.key_value_args(kwargs)}")
        else:
            self.bench.chdir()
            self.bench.invoke(workload_type, **kwargs)
        return self

    def get_traces(self):
        """Downloads distributed request traces for the previous invocation."""
        self.check_bench_init()
        if(not self.local):
            self.run_in_docker('get_traces', local=True)
        else:
            self.bench.chdir()
            self.bench.save_config_to_logs()
            self.bench.save_workload_options_to_logs()
            trace_downloader = None
            if self.bench.spec['provider'] == 'aws':
                trace_downloader = AwsTraceDownloader(self.bench.spec)
            elif self.bench.spec['provider'] == 'azure':
                trace_downloader = AzureTraceDownloader(self.bench.spec)
            else:
                logging.error('Unsupported provider for trace downloader')
            trace_downloader.get_traces()
            self.bench.fix_permissions()
        return self

    def analyze_traces(self, log_path=None):
        """Creates a trace breakdown analysis with the output files:
        * trace_breakdown.csv for valid traces
        * invalid_traces.csv for invalid traces (e.g., incomplete)
        log_path: path to `traces.json` file with one trace per line.
                  Defaults to last invocation if not provided."""
        # Default to last execution if no log path provided
        if log_path is None:
            self.check_bench_init()
            logs_directory = self.bench.spec.logs_directory()
            log_path = logs_directory.joinpath('traces.json')
        trace_analyzer = AwsTraceAnalyzer(log_path)
        trace_analyzer.analyze_traces()
        return self

    def fix_permissions(self):
        """Restores host permissions because a container running as root
        might have created files and directories owned by a root user.
        Recursively chowning the mounted directory fixes the permissions on the host."""
        if self.bench.spec.host_system() != 'Linux':
            return self
        self.check_bench_init()
        if(not self.local):
            self.run_in_docker('fix_permissions', local=True)
        else:
            self.bench.chdir()
            self.bench.fix_permissions()
        return self

    def cleanup(self):
        """Delete all cloud resources."""
        self.check_bench_init()
        if(self.docker):
            self.run_in_docker('cleanup', restore_config=False)
        else:
            # Run all cleanup commands even if some fail
            BenchmarkSpec.CHECK_RETURNCODE_DEFAULT = False
            self.bench.chdir()
            self.bench.cleanup()
            BenchmarkSpec.CHECK_RETURNCODE_DEFAULT = True
        return self

    def validate(self):
        """Check if the *_benchmark.py plugin is valid."""
        self.check_bench_init()
        if(self.docker):
            self.run_in_docker('validate')
        else:
            self.bench.validate()
        return self

    def run_in_docker(self, method, restore_config=True, local=None):
        """Invokes the sb tool within a Docker environment
        with bindmounting the benchmark code and provider credentials."""
        self.check_bench_init()
        self.bench.save_config()
        host_root_path = self.bench.spec.host_root_path()
        mount_dir = f"/apps/{host_root_path.name}"
        bench_dir = f"/apps/{self.bench.spec.sub_path()}"
        bench_file = f"{bench_dir}/{self.bench.file_path.name}"
        code_mount = ''
        interactive_tty = ''
        if(self.debug):
            # Disable tty for tests
            if 'PYTEST_CURRENT_TEST' not in os.environ:
                interactive_tty = ' --interactive --tty'
            # NOTE: This will fail if sb is invoked from within Docker (e.g., in CI env)
            # because sb_root needs to be a mountable path from the Docker host machine
            sb_root = win_vol(Sb.sb_root())
            code_mount = f" -v '{sb_root}':/sb"
        # Docker mode mounts the docker socket from the host.
        # This allows containers to use Docker themselves.
        docker_socket = ''
        if self.docker:
            docker_socket = " -v /var/run/docker.sock:/var/run/docker.sock"
        # For Linux hosts, reading uid from shell fixes file access permissions
        user_permissions = ''
        if(platform.system() == 'Linux'):
            # Need to run container as root until docker supports non-root volumes:
            # https://github.com/moby/moby/issues/2259
            if True or self.docker:
                # Running the container as root user to ensure access to the Docker socket
                # Warning: Files created within the Docker context will have wrong permissions
                # as described here: https://vsupalov.com/docker-shared-permissions/
                # Workaround: chown -R hostuser:hostgroup bench_dir
                user_permissions = ' -u root'
            else:
                user_permissions = self.bench.spec.user_permissions()
        # Notes on Windows volume mount compatibility: https://stackoverflow.com/a/61441015/6875981
        # Allow overwriting the local flag for methods running in the sb container by default.
        local_flag = self.local
        if local is not None:
            local_flag = local
        docker_cmd = (
            f"docker run --rm"
            f"{interactive_tty}"  # Allows attaching an interactive debug console
            f"{code_mount}"
            f"{self.bench.spec.secrets_mount()}"
            f" -v '{win_vol(host_root_path)}':{mount_dir}"
            f"{docker_socket}"
            f"{user_permissions}"
            f" {SB_IMAGE}"
            f" sb {method} --file='{bench_file}' --log_level={self.log_level}"
            f" --local={local_flag} --docker=False"
        )
        logging.info(f"docker={docker_cmd}")
        # MAYBE: implement more robust subprocess invocation with log streaming and
        # providing error traces from within the Docker context
        status = os.system(docker_cmd)
        if status != 0:
            err_msg = (
                f"Error during sb execution of benchmark {self.bench.name}."
                f" Full Docker command:\n{docker_cmd}"
            )
            raise Exception(err_msg)
        # Reload potential updates from inner local execution
        if restore_config:
            self.bench.restore_config()

    def shell(self, image=SB_IMAGE, shell='/bin/bash'):
        """Opens an interactive shell with bindmounting the benchmark code and
        provider credentials in a given container. This mimics the same environment as
        spec.run() to facilitate debugging."""
        self.check_bench_init()
        self.bench.spec.shell(image, shell)
        return self
