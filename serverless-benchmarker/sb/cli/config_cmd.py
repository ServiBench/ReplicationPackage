import json


class ConfigCmd:
    def __init__(self, bench) -> None:
        self.bench = bench
        self.spec = bench.spec

    def show(self):
        conf = self.spec.config
        print(json.dumps(conf, indent=4))

    def get(self, key):
        print(self.spec[key])

    def set(self, key, value):
        self.spec[key] = value
        self.bench.save_config()
