# FAQ

## [docker windows] Shared Windows file into WSL 2 container

Problem: The following Docker Desktop [notification](https://stackoverflow.com/questions/64484579/docker-desktop-filesharing-notification-about-poor-performance) appears when running `sb` on Windows:

> Docker Desktop has detected that you shared a Windows file into a WSL 2 container, which may perform poorly. Click here for more details.

Solution:

Your application currently resides in the Windows file system leading to poor performance.
If this is an issue, you can move your application repo to a WSL 2 path (e.g., `~/my-project`)
as suggested in [Docker Desktop: WSL 2 Best practices](https://www.docker.com/blog/docker-desktop-wsl-2-best-practices/) to get the best performance.

## [aws] Role cannot assumed by Lambda

Problem: `lambda-test.py` fails due to non-existing IAM role

```none
./lambda-test.py --aws_uid $AWS_ACCOUNT_UID --filename function.zip --function-name FaasBench
Traceback (most recent call last):
  File "./lambda-test.py", line 36, in create_function
    response = l.get_function(FunctionName=function_name)
  File "/Users/anonymous/.pyenv/versions/3.6.8/lib/python3.6/site-packages/botocore/client.py", line 357, in _api_call
    return self._make_api_call(operation_name, kwargs)
  File "/Users/anonymous/.pyenv/versions/3.6.8/lib/python3.6/site-packages/botocore/client.py", line 661, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.errorfactory.ResourceNotFoundException: An error occurred (ResourceNotFoundException) when calling the GetFunction operation: Function not found: arn:aws:lambda:eu-west-1:$AWS_ACCOUNT_UID:function:FaasBench_sync

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "./lambda-test.py", line 107, in <module>
    main()
  File "./lambda-test.py", line 92, in main
    sync_function, async_function = setup_functions(l, args.aws_uid, args.filename, args.function_name, args.dlq)
  File "./lambda-test.py", line 54, in setup_functions
    create_function(l, aws_uid, filename, sync_function)
  File "./lambda-test.py", line 43, in create_function
    Role=role_string)
  File "/Users/anonymous/.pyenv/versions/3.6.8/lib/python3.6/site-packages/botocore/client.py", line 357, in _api_call
    return self._make_api_call(operation_name, kwargs)
  File "/Users/anonymous/.pyenv/versions/3.6.8/lib/python3.6/site-packages/botocore/client.py", line 661, in _make_api_call
    raise error_class(parsed_response, operation_name)
botocore.errorfactory.InvalidParameterValueException: An error occurred (InvalidParameterValueException) when calling the CreateFunction operation: The role defined for the function cannot be assumed by Lambda.
make: *** [test] Error 1
```

Solution: Create a IAM role called `lambda_execution_role` with a trust policy that allows assuming the role for the Lambda service.

## [google] Required 'deploymentmanager.deployments.list' permission

Problem: `sls deploy` fails with the following error:

```none
Error --------------------------------------------------

  Error: Required 'deploymentmanager.deployments.list' permission for 'projects/faas-benchmark'
      at Gaxios._request (/Users/anonymous/Projects/Serverless/spec-faas-benchmark/benchmarks/cpustress/google/nodejs/node_modules/gaxios/src/gaxios.ts:109:15)
      at processTicksAndRejections (internal/process/task_queues.js:85:5)
      at JWT.requestAsync (/Users/anonymous/Projects/Serverless/spec-faas-benchmark/benchmarks/cpustress/google/nodejs/node_modules/google-auth-library/build/src/auth/oauth2client.js:346:18)
```

Solution: Wrong project name. Double-check project name carefully.
Re-create project/keys with permissions as documented in the Serverless [credentials docs](https://serverless.com/framework/docs/providers/google/guide/credentials/).
The error message is quite confusing and has a lengthy discussion on [Github](https://github.com/serverless/serverless-google-cloudfunctions/issues/52).
