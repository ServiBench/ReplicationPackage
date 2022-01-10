import os
from timeit import default_timer as timer

def setup():
    os.system('sls deploy')
    # TODO: need a harness-supported way of injecting credentials for all sls calls
    # os.system('sls deploy --credentials=/path/to/credentials.json')

def pre_execute():
    print('needed?')

def execute():
    print('executing')
    os.system('sls invoke --function google-cpustress-nodejs --data \'{ "level": 2 }\'')

def post_execute():
    os.system('cat response.json')

def cleanup():
    os.system('sls remove')

def main():
    setup()

    print('Cold start')
    start = timer()
    execute()
    end = timer()
    print(end - start)

    print('Warm start')
    start = timer()
    execute()
    end = timer()
    print(end - start)

    cleanup()

if __name__ == "__main__":
    main()
