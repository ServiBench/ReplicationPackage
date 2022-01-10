# Output Sample Results

* Date: 2020-02-12
* Purpose: demonstration of result output format
* Client Device: MacBook Pro
* Client Location: Gothenburg, Sweden
* Cloud Region: `eu-west-1` Ireland
* Ping: ~140ms (over 4G)
  * CLI: `ping dynamodb.eu-west-1.amazonaws.com`
  * Online: https://www.cloudping.info/

## cpustress/aws/nodejs

```none
python cpustress_benchmark.py
Serverless: Packaging service...
Serverless: Excluding development dependencies...
Serverless: Creating Stack...
Serverless: Checking Stack create progress...
........
Serverless: Stack create finished...
Serverless: Uploading CloudFormation file to S3...
Serverless: Uploading artifacts...
Serverless: Uploading service cpustress.zip file to S3 (1.63 KB)...
Serverless: Validating template...
Serverless: Updating Stack...
Serverless: Checking Stack update progress...
............
Serverless: Stack update finished...
Service Information
service: cpustress
stage: dev
region: eu-west-1
stack: cpustress-dev
resources: 5
api keys:
  None
endpoints:
  None
functions:
  aws-cpustress-nodejs: aws-cpustress-nodejs
layers:
  None
Serverless: Run the "serverless" command to setup monitoring, troubleshooting and testing.
# Cold start via `aws lambda invoke`
{
    "reused": false,
    "duration": 59334745
}
2.656704437000002
# Warm start via `sls invoke`
{
    "reused": true,
    "duration": 49983496
}
2.189993957999988
# Warm start via `aws lambda invoke`
{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
0.9207338389999933
{"reused":true,"duration":36797318}{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
0.931087938999994
{"reused":true,"duration":36720075}{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
1.1980288880000103
{"reused":true,"duration":53335000}{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
0.8543342390000106
{"reused":true,"duration":36867138}{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
0.9951630369999975
{"reused":true,"duration":36969398}{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
0.8712634899999898
{"reused":true,"duration":38434079}{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
0.9442648410000061
{"reused":true,"duration":37225364}{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
0.8494256769999993
{"reused":true,"duration":38448262}{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
0.97288205400001
{"reused":true,"duration":36905369}{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
0.9981659800000102
{"reused":true,"duration":32599285}Serverless: Getting all objects in S3 bucket...
Serverless: Removing objects in S3 bucket...
Serverless: Removing Stack...
Serverless: Checking Stack removal progress...
..........
Serverless: Stack removal finished...
```

## direct_trigger/aws/go

```none
python direct_trigger_benchmark.py
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
updating: main (deflated 49%)
INFO:root:Results for 10 synchronous function invocations:
INFO:root:Local Invocation Time: 2020-02-12 23:42:26.992857+01:00, Platform Invocation Time: 2020-02-12 22:42:27.560418+00:00, Delta: 0:00:00.567561
INFO:root:Local Invocation Time: 2020-02-12 23:42:27.632460+01:00, Platform Invocation Time: 2020-02-12 22:42:28.031516+00:00, Delta: 0:00:00.399056
INFO:root:Local Invocation Time: 2020-02-12 23:42:28.073683+01:00, Platform Invocation Time: 2020-02-12 22:42:28.133155+00:00, Delta: 0:00:00.059472
INFO:root:Local Invocation Time: 2020-02-12 23:42:28.173270+01:00, Platform Invocation Time: 2020-02-12 22:42:28.232587+00:00, Delta: 0:00:00.059317
INFO:root:Local Invocation Time: 2020-02-12 23:42:28.272115+01:00, Platform Invocation Time: 2020-02-12 22:42:28.322209+00:00, Delta: 0:00:00.050094
INFO:root:Local Invocation Time: 2020-02-12 23:42:28.361370+01:00, Platform Invocation Time: 2020-02-12 22:42:28.422223+00:00, Delta: 0:00:00.060853
INFO:root:Local Invocation Time: 2020-02-12 23:42:28.462115+01:00, Platform Invocation Time: 2020-02-12 22:42:28.521772+00:00, Delta: 0:00:00.059657
INFO:root:Local Invocation Time: 2020-02-12 23:42:28.560820+01:00, Platform Invocation Time: 2020-02-12 22:42:28.621969+00:00, Delta: 0:00:00.061149
INFO:root:Local Invocation Time: 2020-02-12 23:42:28.661315+01:00, Platform Invocation Time: 2020-02-12 22:42:28.712542+00:00, Delta: 0:00:00.051227
INFO:root:Local Invocation Time: 2020-02-12 23:42:28.753327+01:00, Platform Invocation Time: 2020-02-12 22:42:28.813270+00:00, Delta: 0:00:00.059943
```

## api_trigger/aws/go

```none
python api_trigger_benchmark.py
INFO:botocore.credentials:Found credentials in shared credentials file: ~/.aws/credentials
updating: main (deflated 49%)
INFO:root:Created REST API: api_trigger, ID: rguuouq4kh
INFO:root:API base URL: https://rguuouq4kh.execute-api.eu-west-1.amazonaws.com/staging/test
INFO:root:API Gateway bound to lambda function: https://rguuouq4kh.execute-api.eu-west-1.amazonaws.com/staging/test
INFO:root:Start 2020-02-12 23:45:37.624099, End 2020-02-12 23:45:38.325062, delta 700.963 ms
INFO:root:Start 2020-02-12 23:45:38.325223, End 2020-02-12 23:45:38.634576, delta 309.353 ms
INFO:root:Start 2020-02-12 23:45:38.634749, End 2020-02-12 23:45:38.953222, delta 318.473 ms
INFO:root:Start 2020-02-12 23:45:38.953364, End 2020-02-12 23:45:39.295232, delta 341.868 ms
INFO:root:Start 2020-02-12 23:45:39.295457, End 2020-02-12 23:45:39.591740, delta 296.283 ms
INFO:root:Start 2020-02-12 23:45:39.591914, End 2020-02-12 23:45:39.890462, delta 298.548 ms
INFO:root:Start 2020-02-12 23:45:39.890625, End 2020-02-12 23:45:40.210318, delta 319.693 ms
INFO:root:Start 2020-02-12 23:45:40.210487, End 2020-02-12 23:45:40.537212, delta 326.725 ms
INFO:root:Start 2020-02-12 23:45:40.537350, End 2020-02-12 23:45:40.856238, delta 318.888 ms
INFO:root:Start 2020-02-12 23:45:40.856671, End 2020-02-12 23:45:41.178977, delta 322.306 ms
INFO:root:Deleted REST API: api_trigger, ID: rguuouq4kh
```
