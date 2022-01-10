'use strict';

const util = require('util');

exports.handler = (event, context, callback) => {

    var title = "";
    var message = "";

    if (event["errorInfo"]) {
        title = event["errorInfo"]["Error"];
        var errorCause = JSON.parse(event["errorInfo"]["Cause"]);
        message = errorCause["errorMessage"];
    }

    callback(null, {"messageToSend": {"title": title, "message": message}})

};
