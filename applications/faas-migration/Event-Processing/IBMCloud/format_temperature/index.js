'use strict';

const openwhisk = require('openwhisk')
const push = async function(args, topic, message) {
  console.log("Submitting Message")
  console.log(JSON.stringify(message))
  return openwhisk().actions.invoke({actionName: args.binding_name+"/messageHubProduce", params: {topic: topic, value: JSON.stringify(message)}});
}

exports.main =  async function(args) {
  let params = args;
  console.log(JSON.stringify(args));

  var msgs = params.messages; 
  var results = [];
  console.log("Got "+msgs.length+" Messages");
  for (var i = 0; i < msgs.length; i++) {
    var tempEvent = msgs[i].value;

    console.log("processing message #"+i);
    console.log(JSON.stringify(tempEvent));

    let message = "Measured Temperature "+ tempEvent.value + " on device "+  tempEvent.source;

    let evt = {
      type: tempEvent.type,
      source: tempEvent.source,
      timestamp: tempEvent.timestamp,
      formatting_timestamp: getUnixTime(),
      message: message
    }

    let messageString = JSON.stringify(evt);
    console.log(messageString);
    results.push(evt);
  }
  for(let e of results) {
    console.log("Sending Message")
    push(args,"db-ingest",e);
  }
 
  return {
  };
}
const getUnixTime = () => {
  return new Date().getTime()/1000|0
}