'use strict';

const openwhisk = require('openwhisk')
const push = async function(args, topic, message) {
  console.log("Submitting Message")
  console.log(JSON.stringify(message))
  return openwhisk().actions.invoke({actionName: args.binding_name+"/messageHubProduce", params: {topic: topic, value: JSON.stringify(message)}});
}

exports.main =  async function(args) {
  console.log(JSON.stringify(args));

  let message = args;

  let topic = "";

  if(message.type === undefined) {
    return{
      statuscode: 400,
      headers: {
        "Content-Type": "application/json"
      },
      body: {}
    }
  } else if (message.type === "temperature"){
    topic = "temperature";
  } else if (message.type === "forecast") {
    topic = "forecast";
  } else if (message.type === "status_change"|| message.type === "state_change") {
    topic = "state-change";
  } else {
    return{
      statuscode: 400,
      headers: {
        "Content-Type": "application/json"
      },
      body: {}
    }
  }

  message.__ow_headers = null;

  push(args,topic,message);

  let result = {};

  return {
      statuscode: 200,
      headers: {
        "Content-Type": "application/json"
      },
      body: result
  };
}
