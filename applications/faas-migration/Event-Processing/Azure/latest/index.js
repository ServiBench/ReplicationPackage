'use strict';

module.exports.handler = async function (context, req) {
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

  let result = await mysql.query({
    sql: 'SELECT * FROM events ORDER BY ID DESC LIMIT 1;',
    timeout: 10000
  });
  context.log(result);
  await mysql.end();

  context.res = {
      status: 200,
      body: JSON.stringify(result)
  };
};