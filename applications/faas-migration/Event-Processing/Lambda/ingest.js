'use strict';


// Instrument aws client: https://docs.aws.amazon.com/lambda/latest/dg/nodejs-tracing.html
const AWSXRay = require('aws-xray-sdk-core')
const aws = AWSXRay.captureAWS(require('aws-sdk'))

const sns = new aws.SNS({ region: process.env.CLOUD_REGION })

module.exports.handleIngest = async (event) => {
  const fail = () => {
    return {
      statusCode: 400,
      body: JSON.stringify({
        message: 'Invalid Data Type',
      }, null, 2),
    };
  };

  let message = JSON.parse(event.body);
  let topic = "";

  if(message.type === undefined) {
    return fail();
  } else if (message.type === "temperature"){
    topic = process.env.TEMPERATURE_TOPIC_ARN;
  } else if (message.type === "forecast") {
    topic = process.env.FORECAST_TOPIC_ARN;
  } else if (message.type === "status_change"|| message.type === "state_change") {
    topic = process.env.STATE_CHANGE_TOPIC_ARN;
  } else {
    return fail();
  }

  let snsParams =  {
    Message: JSON.stringify(message),
    TopicArn: topic
  };
  let result = await sns.publish(snsParams).promise();
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Pushed!',
        result: result,
        topic: topic
    }, null, 2),
  };
};