BENCHMARK_CONFIG = """
todo_api:
  description: API for a todo list manager application
  provider: azure
  region: eastus
  root: ..
  resource_group: faas-migration
  storage_acc_name: cmuellertodostore
  app_name: cmueller-bt-todo-api
  app_insights_name: cmuellertodoai
"""
import os

TAG = 'deps_with_azure_cli'


def prepare(spec):
    spec.build(TAG)

    deploy_cmd = f"make deploy {make_vars(spec)}"
    spec.run(deploy_cmd, image=TAG)


def make_vars(spec):
    """Returns configurable variables for make"""
    return f"AZURE_REGION={spec['region']} RESOURCE_GROUP_NAME={spec['resource_group']} STORAGE_ACCOUNT_NAME={spec['storage_acc_name']} FUNCTION_APP_NAME={spec['app_name']} APPINSIGHTS_NAME={spec['app_insights_name']}"


def invoke(spec):
    #/del, /done, /get, /lst, /put
    invoke_urls = fetch_url_from_log("prepare_log.txt")
    #/
    spec['endpoint'] = invoke_urls[0].split('/api/')[0] + '/api'
    envs = {
        'URL': spec['endpoint']
    }
    spec.run_k6(envs)


def fetch_url_from_log(filename):
    invoke_urls = []
    prefix = "        Invoke url: "
    with open(filename) as f:
        for line in f:
            if line.startswith(prefix):
                url = line.replace(prefix, '')
                url = url.replace('\n', '')
                invoke_urls.append(url)
    return invoke_urls


def cleanup(spec):
    spec.run(f"make cleanup {make_vars(spec)}", image=TAG)
    #remove the invoke_url.txt file
    url_file = 'prepare_log.txt'
    if os.path.exists(url_file):
        os.remove(url_file)
