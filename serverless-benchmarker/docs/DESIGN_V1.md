# Design V1

## Add your application to serverless-benchmarker (sb)

1. Create a `*_benchmark.py` in the main directory of your application.
2. Implement hooks as shown under Hooks API below.
3. Provide a `Dockerfile` that specifies all build and deployment dependencies.
4. Instrument app with trace log statements

### Hooks API

```python
BENCHMARK_CONFIG = """
mock_benchmark:
  description: Short description of your application.
  provider: aws
  region: us-east-1
  endpoint: DYNAMIC
"""

def prepare(spec):
    os.system('sls deploy')

def invoke(spec):
    os.system('aws lambda invoke --region=eu-west-1 --function aws-cpustress-nodejs --payload \'{ "level": 2 }\' response.json')

def cleanup(spec):
    os.system('sls remove')
```

### Instrumentation

```none
<unix epoch time in ms with time zone>|LABEL
1600776870140+0000|PRE_INVOKED

# sh (Linux only; doesn't work on macOS!)
date +%s%3N%z
1600776870140+0000
```

or use UTC

## Use sb

[1] API inspired by Google's PerfKitBenchmarker for VM benchmarking; see [example](https://github.com/GoogleCloudPlatform/PerfKitBenchmarker/blob/master/perfkitbenchmarker/linux_benchmarks/ping_benchmark.py)
[2] API inspired by GitHub action [workflow commands](https://docs.github.com/en/actions/reference/workflow-commands-for-github-actions)

See Fire docs for potentially relevant features such as [grouping](https://github.com/google/python-fire/blob/master/docs/guide.md#grouping-commands) or [list arguments](https://github.com/google/python-fire/blob/master/docs/guide.md#functions-with-varargs-and-kwargs)

## Notes

* Handle units and their conversion: https://pint.readthedocs.io/en/stable/
* Python decorators: https://realpython.com/primer-on-python-decorators/
* Better validator to check whether mandatory hooks are present:

    ```py
    import inspect
    functions = inspect.getmembers(bench, predicate=inspect.isfunction)
    ```

## Getting Started (ultimately)

* Suites of benchmarks: `sb suite.py` runs a collection of benchmarks with a given schedule

* Out of the box benchmarks referenced through shortnames:

```sh
sb test --benchmarks=thumbnail_generator
```

```sh
sb test --benchmarks=thumbnail_generator --cloud=azure --region='East US'
```
