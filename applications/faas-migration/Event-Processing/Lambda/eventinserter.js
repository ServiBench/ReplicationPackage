const createDBQuery = "CREATE TABLE IF NOT EXISTS events (ID int unsigned NOT NULL auto_increment PRIMARY KEY, source VARCHAR(255) NOT NULL, timestamp int unsigned NOT NULL, message VARCHAR(1000) NOT NULL);"

// Instrument mysql client: https://www.npmjs.com/package/aws-xray-sdk-mysql#automatic-mode-example
var AWSXRay = require('aws-xray-sdk-core');
var captureMySQL = require('aws-xray-sdk-mysql');

const mysql = require('serverless-mysql')({
  config: {
    database: process.env.RDS_DB_NAME,
    user: process.env.RDS_USERNAME,
    password: process.env.RDS_PASSWORD,
    host: process.env.RDS_HOST,
    port: process.env.RDS_PORT,
    // X-Ray instrumentation: https://www.npmjs.com/package/serverless-mysql#custom-libraries
    library: captureMySQL(require('mysql'))
  }
});

module.exports.insertEvent = async (event) => {
  let creationResult = await mysql.query(createDBQuery);
  const evt= JSON.parse(event.Records[0].body);

  // Submit XRay trace ID from previous trace due to lacking SQS support (https://github.com/aws/aws-xray-sdk-node/issues/208)
  AWSXRay.captureFunc('annotations', function(subsegment) {
    subsegment.addAnnotation('root_trace_id', String(evt.trace_id));
  });

  // console.log(creationResult);
  // console.log(JSON.stringify(evt));
  let insertResult = await mysql.query({
    sql: 'INSERT INTO events(source, timestamp, message) VALUES (?, ?, ?);',
    timeout: 10000,
    values: [evt.source, evt.timestamp, evt.message]
  });
  // console.log(insertResult);
  await mysql.end();
  return {};
};