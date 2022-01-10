# Event-Processing -  Use-Case

This Directory contains the implementations of the Event Processing Use-Case.

## Running the Tests

To run the tests, esure the Go SDK is installed. After that the tests can be executed by running the following command in this directory:

```bash
go run *.go -endpoint <API Endpoint> -delay <Delay> -count <Count>
```

The tests assume the implemeńtation you want to test is already deployed. To do so follow the instructions in the directories of the
implementations.

The parameters of the test have the following purposes:

- `endpoint`: Defines the path to the Exposed api. E.g. `https://5f4snin1r2.execute-api.us-east-1.amazonaws.com/dev` on AWS. It is important to only keep the part that is always identical between the functions, since the test will use the url to build the urls to the specific functions. This parameter is **required**.
- `delay`: Defines the delay between the insertion and the validation in seconds. Setting this is **optional** if it is unset the default of 90 (Seconds) will be used.
- `count`: The number of insertions the test should perform for each event type. This is also **optional** the default is 50.

### Side Note

When running the tests ourselves we were experiencing a failure rate on AWS meaning that some messages have gone missing. Increasing the delay did not resolve the problem. The cause is not known to us however we did not investigate thsi problem further.

Such a problem did not exist on Azure. There All events where processed. No losses occured.

This table shows a small overview on the failure counts we have experienced on AWS:

| Number of Events | Fails |
| - | -|
| 90 | 30 |
| 150 | 24 |
| 300 | 30 |
| 900 | 30 |
| 1.500 | 64 |

## Application Specification

This application exposes 3 HTTP functions:

- `POST /ingest` - Used to submit events
- `GET /list` - Used to get a list of all processed events in the database
- `GET /latest`- Used to get the latest element in the database

All these functions respond with the status code 200 if everything worked as expected. Otherwise
an error code is returned. What type of error is not defined further.

### `ingest` Function

The Ingest function accepts Events of three types (Type definition is below); Temperature, Forecast
and State Change Depending on the input event it will publish the event on a different topic to handle formatting.

The events have to be submitted as JSON objects.

### `list` Function

Returns a List, Encoded as json, of all the ProcessedEvents

### `latest` Function

Returns a list of either one Processed event, beeing the latest or none if no events have been inserted. Encoded as JSON.

### Sample Models

#### Forecast Event

```json
{
  "type": "state_change",
  "source": "opweeyozkbvoddlfqnzqjwbhxdnvot",
  "timestamp": 1566246,
  "forecast": 123,
  "forecast_for": "hello world",
  "place": "myplace"
}
```

- `type`: Always `temperature`
- `source`: The name of the source that created the measurement
- `timestamp`: Unix Timestamp (in Seconds) when the event occured
- `forecast`: The value (temperature) forecasted
- `forecast_for`: String representation of the timestamp for which the forecast applies
- `place`: the place for which the forecast applies


#### Temperature Event

```json
{
  "type": "temperature",
  "source": "opweeyozkbvoddlfqnzqjwbhxdnvot",
  "timestamp": 1566246,
  "value": 162
}
```

- `type`: Always `temperature`
- `source`: The name of the source that created the measurement
- `timestamp`: Unix Timestamp (in Seconds) when the event occured
- `value`: The "measured" value

#### StateChange Event

```json
{
  "type": "state_change",
  "source": "opweeyozkbvoddlfqnzqjwbhxdnvot",
  "timestamp": 1566246,
  "message": "mymessage"
}
```

- `type`: Always `temperature`
- `source`: The name of the source that created the measurement
- `timestamp`: Unix Timestamp (in Seconds) when the event occured
- `message`: A message describing the State change

#### ProcessedEvent

```json
{
  "ID": 10,
  "source": "opweeyozkbvoddlfqnzqjwbhxdnvot",
  "timestamp": 1566246,
  "message": "mymessage"
}
```

- `ID`: The ID of the event.
- `source`: The name of the source that created the event
- `timestamp`: Unix Timestamp (in Seconds) when the event occured
- `message`: the formatted message
