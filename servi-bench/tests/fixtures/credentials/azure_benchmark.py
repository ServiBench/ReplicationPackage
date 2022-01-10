import logging
import json

BENCHMARK_CONFIG = """
azure_benchmark:
  provider: azure
"""


def prepare(spec):
    check_azure(spec)


def check_azure(spec):
    azure = spec.run('az account show', image='azure_cli')
    azure_json = json.loads(azure)
    id = azure_json["id"]
    logging.info(f"id={id}")
    assert azure_json['state'] == 'Enabled'


def invoke(spec):
    pass


def cleanup(spec):
    pass
