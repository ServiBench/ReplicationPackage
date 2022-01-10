import logging

BENCHMARK_CONFIG = """
count_api:
  description: A simple REST API that counts the number of times a route has been hit.
  provider:
  - aws
  - pulumi
  region: us-east-1
"""
STACK = 'count-api-testing'


def prepare(spec):
    # Make this command idempotent (i.e., don't fail if stack already exists)
    try:
        spec.run(f"pulumi stack init {STACK}", image='pulumi_cli')
    except:
        logging.warn(f"Error initializing a new Pulumi Stack. Does it already exist?")
    spec.run(f"pulumi config set aws:region {spec['region']}", image='pulumi_cli')
    spec.run('npm install', image='node12.x')
    spec.run('pulumi up --yes', image='pulumi_cli')
    spec['endpoint'] = spec.run('pulumi stack output endpoint', image='pulumi_cli').rstrip()
    logging.info(f"endpoint={spec['endpoint']}")


# TODO: Add XRay instrumentation to Pulumi code for full sb support
def invoke(spec):
    url = f"{spec['endpoint']}/hello"
    # NOTE: automatic load pattern injection WIP
    spec.run(f"k6 run -e \"URL={url}\" load_script.js", image = 'loadimpact/k6:0.30.0')


def cleanup(spec):
    spec.run(f"pulumi stack select {STACK}", image='pulumi_cli')
    spec.run('pulumi destroy --yes', image='pulumi_cli')
    spec.run('pulumi stack rm --yes --force', image='pulumi_cli')
