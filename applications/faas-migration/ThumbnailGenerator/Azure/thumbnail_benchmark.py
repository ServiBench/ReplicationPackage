BENCHMARK_CONFIG = """
thumbnail_generator:
  description: Generates a thumbnail every time an image is uploaded to object storage.
  provider: azure
  region: westeurope
  root: ..
  resource_group: faas-migration-v2
  app_name: cmueller-bt-thumbnail-generator-v2
"""

# TODO: Check which resource names need to have a random deploy suffix to prevent issues if multiple versions of the app are deployed globally

TAG = 'maven-with-azure-cli'


def prepare(spec):
    spec.build(TAG)
    envs = (
        f"APP_NAME={spec['app_name']} "
        f"RG={spec['resource_group']} "
        f"AZ={spec['region']}"
    )
    mvn_cmd = f"{envs} mvn clean install 'azure-functions:deploy' --no-transfer-progress"
    spec.run(mvn_cmd, image=TAG)
    con_cmd = (
        f"az functionapp config appsettings list "
        f"-g {spec['resource_group']} -n {spec['app_name']} "
        f"""--query "[?name=='AzureWebJobsStorage'].value" --output tsv"""
    )
    storage_config = spec.run(con_cmd, image=TAG).rstrip()
    out_cmd = f"az storage container create -n output --connection-string '{storage_config}'"
    spec.run(out_cmd, image=TAG)
    in_cmd = f"az storage container create -n input --connection-string '{storage_config}'"
    spec.run(in_cmd, image=TAG)


def invoke(spec):
    filename = 'img.png'
    invoke_cmd = f"""cat ../test-images/test-1.png | base64 | curl -v -d @- "https://{spec['app_name']}.azurewebsites.net/api/Upload-Image?name={filename}" """
    spec.run(invoke_cmd, image='curlimages/curl:7.73.0')


def cleanup(spec):
    spec.run(f"az group delete --name {spec['resource_group']} --yes", image=TAG)
