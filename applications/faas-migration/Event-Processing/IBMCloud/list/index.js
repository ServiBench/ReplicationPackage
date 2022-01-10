'use strict';

const createDBQuery = "CREATE TABLE IF NOT EXISTS events (ID int unsigned NOT NULL auto_increment PRIMARY KEY, source VARCHAR(255) NOT NULL, timestamp int unsigned NOT NULL, message VARCHAR(1000) NOT NULL);"

const parseDatabaseCredentials = function(args) {
  let dburl = args.uri.toString().replace("mysql://","");
  let spliturl = dburl.split("@");
  let creds = spliturl[0].split(":");
  let username = creds[0];
  let password = creds[1];
  let hostDb = spliturl[1].split("/");
  let hostnamePort = hostDb[0].split(":");
  let hostname = hostnamePort[0];
  let port = hostnamePort[1];
  let db = hostDb[1];

  return {
    user: username,
    pass: password,
    db: db,
    host: hostname,
    port: parseInt(port, 10)
  };
}

exports.main =  async function(args) {
  let params = args;
  console.log(JSON.stringify(args));

  let creds = parseDatabaseCredentials(args);

  const mysql = require('serverless-mysql')({
    config: {
      database: creds.db,
      user: creds.user,
      password: creds.pass,
      host: creds.host,
      port: creds.port,
      ssl: {
        rejectUnauthorized: false
      }
    }
  });
  await mysql.query(createDBQuery);

  let result = await mysql.query({
    sql: 'SELECT * FROM events ORDER BY ID DESC;',
    timeout: 10000
  });
  console.log(result);
  await mysql.end();

  return {
      statuscode: 200,
      headers: {
        "Content-Type": "application/json"
      },
      body: result
  };
}