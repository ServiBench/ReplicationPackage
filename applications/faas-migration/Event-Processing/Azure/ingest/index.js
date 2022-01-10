'use strict';

module.exports.handler = async function (context, req) {
    const fail = () => {
        context.res = {
            status: 400,
            body: JSON.stringify({message:"Invalid Message!"})
        };
    };
    
    let message = req.body;
    let messageString = JSON.stringify(message);
    
    if(message.type === undefined) {
      return fail();
    } else if (message.type === "temperature"){
      context.bindings.temperatureTopic = messageString;
    } else if (message.type === "forecast") {
      context.bindings.forecastTopic = messageString;
    } else if (message.type === "status_change"|| message.type === "state_change") {
      let messageString = JSON.stringify(message);context.bindings.stateChangeTopic = messageString;
    } else {
      fail();
      return;
    }
    context.res = {
        status: 200,
        body: JSON.stringify({message:"Pushed!"})
    };
};