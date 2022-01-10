'use strict';

module.exports.handler = async function (context, item) {
  const createDBQuery = "CREATE TABLE IF NOT EXISTS events (ID int unsigned NOT NULL auto_increment PRIMARY KEY, source VARCHAR(255) NOT NULL, timestamp int unsigned NOT NULL, message VARCHAR(1000) NOT NULL);"

  const mysql = require('serverless-mysql')({
    config: {
      database: process.env.DBName,
      user: process.env.DBUsername,
      password: process.env.DBPassword,
      host: process.env.DBEndpoint,
      port: 3306,
      ssl: {
        rejectUnauthorized: false
      }
    }
  });

  await mysql.query(createDBQuery);
  let evt = item;
  let insertResult = await mysql.query({
    sql: 'INSERT INTO events(source, timestamp, message) VALUES (?, ?, ?);',
    timeout: 10000,
    values: [evt.source, evt.timestamp, evt.message]
  });
  context.log(insertResult);
  await mysql.end();
};