import os
from timeit import default_timer as timer

# TODO: Adjust WIP (not tested)

BENCHMARK_CONFIG = """
cpustress:
  description: Loops over a CPU-intensive math function.
  provider: aws
  region: us-east-1
  endpoint: DYNAMIC
"""

def configure(sb):
    sb.load_config(BENCHMARK_CONFIG)

def prepare(sb):
    os.system(f"sls deploy --region {sb['region']}")

# Faster deployment alternative but incomplete
def prepare_fast(sb):
    # Create role: https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_create_for-service.html#roles-creatingrole-service-cli
    # TODO: need to be more elaborate (e.g., creating lambda role)
    os.system('zip function.zip handler.js && aws lambda update-function-code --function-name aws-cpustress-nodejs --zip-file fileb://function.zip')

# ~1.2s
# Conclusion: Invoking lambda functions through the Serverless Framwework results in too much overhead as it takes double the time
# compared to CLI-based invokcation.
def invoke(sb):
    payload = '{ "level": 2 }'
    os.system(f"aws lambda invoke --region={sb['region']} --function aws-cpustress-nodejs --payload {payload} response.json")

# ~2.4s
def invoke_slow(sb):
    payload = '{ "level": 2 }'
    os.system('sls invoke --function aws-cpustress-nodejs --data {payload}')

def cleanup(sb):
    os.system('sls remove')

# def main():
#     prepare()

#     print('# Cold start via `aws lambda invoke`')
#     start = timer()
#     invoke()
#     end = timer()
#     print(end - start)

#     print('# Warm start via `sls invoke`')
#     start = timer()
#     invoke()
#     end = timer()
#     print(end - start)

#     print('# Warm start via `aws lambda invoke`')
#     num_iterations = 10
#     for _ in range(num_iterations):
#         start = timer()
#         invoke_slow()
#         end = timer()
#         print(end - start)

#     cleanup()

# if __name__ == "__main__":
#     main()
