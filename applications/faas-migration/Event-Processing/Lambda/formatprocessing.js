'use strict';

// Instrument aws client: https://docs.aws.amazon.com/lambda/latest/dg/nodejs-tracing.html
const AWSXRay = require('aws-xray-sdk-core')
const aws = AWSXRay.captureAWS(require('aws-sdk'))

const sqs = new aws.SQS({ region: process.env.CLOUD_REGION })

const getUnixTime = () => {
  return new Date().getTime()/1000|0
}
const getQueueURL = () => {
  return 'https://sqs.'+process.env.CLOUD_REGION+'.amazonaws.com/' +
       process.env.CLOUD_ACCOUNT_ID + '/'+ process.env.QUEUE_NAME;
};

// XRay trace id to pass into queue for next function.
// Using env variable convention from XRay SDK:
// https://github.com/aws/aws-xray-sdk-node/blob/master/packages/core/lib/env/aws_lambda.js#L79
// Example: process.env._X_AMZN_TRACE_ID == "Root=1-6089c2ee-ee6f2517d06abc24fde41c4a;Parent=bf496f08ba12224b;Sampled=1"
const getRootTraceId = () => {
  const traceData = process.env._X_AMZN_TRACE_ID;
  const data = AWSXRay.utils.processTraceData(traceData);
  return data.root;
}

module.exports.formatTemperatureEvent = async (event) => {
  let tempEvent = JSON.parse(event.Records[0].Sns.Message);

  // console.log(JSON.stringify(tempEvent));

  let message = "Measured Temperature "+ tempEvent.value + " on device "+  tempEvent.source;

  let evt = {
    type: tempEvent.type,
    source: tempEvent.source,
    timestamp: tempEvent.timestamp,
    formatting_timestamp: getUnixTime(),
    message: message,
    trace_id: getRootTraceId()
  }

  let messageString = JSON.stringify(evt);
  // console.log(messageString);
  // console.log(getQueueURL());

  var params = {
    MessageBody: messageString,
    QueueUrl: getQueueURL()
  };

  await sqs.sendMessage(params).promise();
};

module.exports.formatForecastEvent = async (event) => {
  let tempEvent = JSON.parse(event.Records[0].Sns.Message);

  // console.log(JSON.stringify(tempEvent));

  let message = tempEvent.source + " has Forecasted " + tempEvent.forecast +
     " at " + tempEvent.place + " for " + tempEvent.forecast_for;

  let evt = {
    type: tempEvent.type,
    source: tempEvent.source,
    timestamp: tempEvent.timestamp,
    formatting_timestamp: getUnixTime(),
    message: message,
    trace_id: getRootTraceId()
  }

  let messageString = JSON.stringify(evt);
  // console.log(messageString);
  // console.log(getQueueURL());

  var params = {
    MessageBody: messageString,
    QueueUrl: getQueueURL()
  };

  await sqs.sendMessage(params).promise();
};

module.exports.formatStateChangeEvent = async (event) => {
  let tempEvent = JSON.parse(event.Records[0].Sns.Message);

  // console.log(JSON.stringify(tempEvent));

  let message = tempEvent.source + " has Submitted a status change with the message "+ tempEvent.message;

  let evt = {
    type: tempEvent.type,
    source: tempEvent.source,
    timestamp: tempEvent.timestamp,
    formatting_timestamp: getUnixTime(),
    message: message,
    trace_id: getRootTraceId()
  }

  let messageString = JSON.stringify(evt);
  // console.log(messageString);
  // console.log(getQueueURL());

  var params = {
    MessageBody: messageString,
    QueueUrl: getQueueURL()
  };

  await sqs.sendMessage(params).promise();
};

module.exports.handleErr = async (event) => {
  let tempEvent = event.Records[0].Sns.Message;
  console.log("Event with Payload has failed! "+ tempEvent);
  return {};
};
