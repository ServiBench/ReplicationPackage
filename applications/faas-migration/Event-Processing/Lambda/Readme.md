# Event-Processing - AWS Implementation

This is the AWS Implementation of the Event Processing use-case.

## Prerequisites

- Serverless Framework CLI with Configured Roles (see [here](/docs/aws_setup.md))
- NodeJS Version 8 or newer

## Deployment

### Step 1: Installing Dependencies

First run `npm install` in the directory of this readme to update the Serverless CLI plugins and the functions dependencies.

### Step 2: Setting Different Credentials (OPTIONAL)

If you want to modify the database credentials or queue names away from the default change them in the custom section of the `serverless.yml`

```yaml
custom:
  # Modify Queue names here
  temperature_format_topic: format-temperature
  forecast_format_topic: format-forecast
  state_change_format_topic: format-state-change
  error_topic: error
  sqs_queue_name: EventIngestQueue
  database:
    # DO NOT CHANGE THIS
    db_name: aurora${opt:stage, self:provider.stage}
    # Set the username of the administrator
    username: master
    # Set the password of the administrator
    password: aCo2xeuph5wahr7s
    # DO NOT CHANGE THE FOLLOWING PARAMETERS
    host:
      Fn::GetAtt: [AuroraRDSCluster, Endpoint.Address]
    port:
      Fn::GetAtt: [AuroraRDSCluster, Endpoint.Port]
    vpc_cidr: 10
```

### Step 3: Deploying

Next run `serverless deploy --verbose` to deploy the function stack. This takes a while (Approyimately between 10 and 30 Minutes) because the provisioning of the RDS instance is very slow.

Also keep in mind the `--verbose` or `-v` option is optional however it gives a better overview on the current deployment progress.

To update the functions just rerun the command. 

## Destroying

Just like any other Serverless Framework base use case run `serverless remove --verbose` to delete the previously deployed stack.
