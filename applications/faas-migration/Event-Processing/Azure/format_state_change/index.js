'use strict';

module.exports.handler = async function (context, item) {
  let tempEvent = item;

  context.log(JSON.stringify(tempEvent));

  let message = tempEvent.source + " has Submitted a status change with the message "+ tempEvent.message;

  let evt = {
    type: tempEvent.type,
    source: tempEvent.source,
    timestamp: tempEvent.timestamp,
    formatting_timestamp: getUnixTime(),
    message: message
  };

  let messageString = JSON.stringify(evt);
  context.log(messageString);

  context.bindings.queueOutput = messageString;
  return;  
};

const getUnixTime = () => {
  return new Date().getTime()/1000|0
}