import yaml
import logging
from pathlib import Path
import importlib.util
import os
import shutil
import platform
import subprocess
from mergedeep import merge

from sb.event_log import EventLog
from sb.benchmark_spec import BenchmarkSpec

HOOKS = ['prepare', 'invoke', 'cleanup']
BENCHMARK_CONFIG = 'BENCHMARK_CONFIG'
SB_DIR = '.sb'
SB_CONFIG = 'config.yml'


class Benchmark:

    def initialize(benchmark_file):
        file_path = Path(benchmark_file).resolve()
        module_name = 'benchmark.plugin'
        plugin = Benchmark.load_module(file_path, module_name)
        bench = Benchmark(plugin, file_path)
        bench.validate()
        bench.load_spec(plugin.BENCHMARK_CONFIG)
        return bench

    def load_module(abs_path, module_name):
        module_spec = importlib.util.spec_from_file_location(module_name, abs_path)
        mod = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(mod)
        return mod

    def __init__(self, plugin, file_path, spec=None):
        self.plugin = plugin
        self.file_path = file_path
        self.path = self.file_path.parent
        self.spec = spec

    @property
    def name(self):
        return self.spec.name

    def validate(self):
        if not hasattr(self.plugin, BENCHMARK_CONFIG):
            raise Exception('Missing variable BENCHMARK_CONFIG')
        for hook in HOOKS:
            if not hasattr(self.plugin, hook):
                raise Exception(f"Missing hook implementation for {hook}")

    def chdir(self):
        """Changes into the benchmark directory"""
        os.chdir(self.path)

    def fix_permissions(self):
        """Linux-only helper to take ownership of the benchmark root directory."""
        if self.spec.host_system() != 'Linux':
            return
        user_group = self.spec.host_user_group() or self.host_user_group()
        path = self.spec['root'] or '.'
        logging.info('Fixing permissions of benchmark root directory ...')
        try:
            subprocess.check_output(['chown', '-R', user_group, path])
        except subprocess.CalledProcessError:
            logging.error('Failed to fix permissions.')

    def prepare(self):
        start = self.log_start('prepare')
        self.save_config()
        logging.info('prepare()')
        self.plugin.prepare(self.spec)
        end = self.log_end('prepare')
        self.save_config()
        logging.info(f"[{self.spec.name}]prepare_time={end - start}")

    def invoke(self, workload_type=None,
               scale_factor=1, scale_type='linear',
               workload_trace=None, workload_options=None,
               seconds_to_skip=3 * 60):
        logging.info('invoke()')
        start = self.log_start('invoke')
        # string comparison handles Docker-mode case where None is passed as string
        if str(workload_type) != 'None':  # CLI param overwrites config
            self.spec['workload_type'] = workload_type
        else:  # Default to single if unspecified
            self.spec['workload_type'] = 'single'
        self.spec['scale_factor'] = scale_factor
        self.spec['scale_type'] = scale_type
        self.spec['workload_trace'] = workload_trace
        self.spec['seconds_to_skip'] = seconds_to_skip

        self.save_config()
        self.spec.create_workload_options_file(self.path, workload_options)
        self.plugin.invoke(self.spec)
        end = self.log_end('invoke')
        self.save_config()
        logging.info(f"[{self.spec.name}]invoke_time={end - start}")

    def cleanup(self):
        logging.info('cleanup()')
        start = self.log_start('cleanup')
        self.save_config()
        self.plugin.cleanup(self.spec)
        end = self.log_end('cleanup')
        self.remove_config()
        logging.info(f"[{self.spec.name}]cleanup_time={end - start}")
        logging.info(f"[{self.spec.name}]total_time={self.spec.event_log.total_duration()}")

    def log_start(self, name):
        return self.spec.event_log.start(name)

    def log_end(self, name):
        return self.spec.event_log.end(name)

    def load_spec(self, yml_config):
        config = dict()
        plugin_config = yaml.safe_load(yml_config)
        # The first top-level key defines the benchmark name by convention
        name = list(plugin_config.keys())[0]
        if self.config_path().is_file():  # prior sb config exists
            loaded_config = self.load_config()
            # Handle special case where plugin config has no attributes
            if plugin_config[name] is None:
                config = loaded_config
            else:
                # Deep merge: plugin config takes precedence over restored config
                config = merge({}, loaded_config, plugin_config)
        else:  # no prior sb config exits
            config = {**plugin_config, **self.new_sb_config()}
            # Initialize dict if benchmark has no yml config
            if config[name] is None:
                config[name] = dict()
            # Initialize event log
            config[name][EventLog.SB_EVENT_LOG] = []
        self.spec = BenchmarkSpec(config, name)

    def new_sb_config(self):
        sb_config = {
            'sb': {
                'host_path': str(self.path.resolve()),
                'host_system': platform.system(),
                'host_user_group': self.host_user_group()
            }
        }
        return sb_config

    def host_user_group(self):
        """Returns the UID of user and group on Linux or None otherwise."""
        if platform.system() == 'Linux':
            try:
                user = subprocess.run(['id', '-u'], capture_output=True, text=True).stdout.strip()
                group = subprocess.run(['id', '-g'], capture_output=True, text=True).stdout.strip()
                return f"{user}:{group}"
            except Exception:
                logging.warning('Failed to detect user and group on Linux host.')
                return None
        return None

    def save_workload_options_to_logs(self):
        """Save a copy of the workload options json to the logs directory"""
        if self.spec.logs_directory():
            _, src = self.spec.workload_file_paths()
            file_name = Path(src).name
            dst = self.spec.logs_directory() / file_name
            shutil.copy(src, dst)

    def save_config_to_logs(self):
        """Save a config copy to the logs directory if an invocation exists."""
        if self.spec.logs_directory():
            config_backup = self.spec.logs_directory() / 'sb_config.yml'
            self.save_config(config_backup)

    def save_config(self, path=None):
        """Persists the spec config to a file, by default the config_path."""
        config_file = self.config_path()
        if path:
            config_file = path
        config_dir = config_file.parent
        config_dir.mkdir(exist_ok=True)
        with open(config_file, 'w') as file:
            yaml.dump(self.spec.config, file)

    def restore_config(self, path=None):
        """Replaces the current config with the config loaded from
        the sb config file without validation or merging precedence rules!
        """
        self.spec.config = self.load_config(path)

    def load_config(self, path=None):
        """Loads and returns the sb configuration from file"""
        config_file = self.config_path()
        if path:
            config_file = path
        with open(config_file) as file:
            return yaml.safe_load(file)

    def remove_config(self):
        """Removes the sb config if the last run command succeeded.
        Motivation: If the last (cleanup) run command failed, we want to
        keep dynamic attributes such as deploy_id for re-tryting automated cleanup later.
        """
        # This condition only checks the last run command executed
        # immediately beforehand and does not persist across CLI invocations.
        # Caveat: it could apply to a run or prepare command if cleanup does
        # not implement a spec.run() command.
        if not self.spec.last_run_success:
            logging.info(f"Skip sb config removal because last run failed. Config path: {self.config_path()}.")  # noqa: E501
            return
        # Otherwise, remove sb config if it exists
        if self.config_path().exists():
            logging.debug(f"Delete sb config at {self.config_path()}.")
            self.config_path().unlink()
        else:
            logging.warning(f"No sb config exists to remove at {self.config_path()}.")

    def config_path(self) -> Path:
        return self.path.joinpath(SB_DIR, SB_CONFIG).resolve()
