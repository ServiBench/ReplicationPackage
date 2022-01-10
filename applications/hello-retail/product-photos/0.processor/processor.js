'use strict'

const AWSXRay = require('aws-xray-sdk-core') // eslint-disable-line import/no-unresolved, import/no-extraneous-dependencies
const aws = AWSXRay.captureAWS(require('aws-sdk')) // eslint-disable-line import/no-unresolved, import/no-extraneous-dependencies
const KH = require('kinesis-handler')

/**
 * AJV Schemas
 */
const eventSchema = require('./retail-stream-schema-egress.json')
const updatePhoneSchema = require('./user-update-phone-schema.json')
const productCreateSchema = require('./product-create-schema.json')

const constants = {
  // self
  MODULE: 'product-photos/0.processor/processor.js',
  // methods
  METHOD_START_EXECUTION: 'startExecution',
  // values
  TTL_DELTA_IN_SECONDS: 60 /* seconds per minute */ * 60 /* minutes per hour */ * 2 /* hours */,
  // resources
  STEP_FUNCTION: process.env.STEP_FUNCTION,
  TABLE_PHOTO_REGISTRATIONS_NAME: process.env.TABLE_PHOTO_REGISTRATIONS_NAME,
}

/**
 * Transform record (which will be of the form in ingress schema) to the form of egress schema
 */
const transformer = (payload, record) => {
  const result = Object.assign({}, payload)
  result.schema = 'com.nordstrom/retail-stream-egress/1-1-0'
  result.eventId = record.eventID
  result.traceId = record.traceId
  result.timeIngest = new Date(record.kinesis.approximateArrivalTimestamp * 1000).toISOString()
  result.timeProcess = new Date().toISOString()
  return result
}

/**
 * Event Processor
 */
const kh = new KH.KinesisHandler(eventSchema, constants.MODULE, transformer)

/**
 * AWS
 */
const dynamo = new aws.DynamoDB.DocumentClient()
const stepfunctions = new aws.StepFunctions()

const impl = {
  /**
   * Parse the origin
   * @param origin
   * @return {*}
   */
  eventSource: (origin) => {
    const parts = origin.split('/')
    if (parts.length > 2) {
      return {
        uniqueId: parts[2],
        friendlyName: parts.length === 3 ? parts[2] : parts[3],
      }
    } else if (parts.length === 2) {
      return {
        uniqueId: parts[1],
        friendlyName: parts[1],
      }
    } else {
      return {
        uniqueId: 'UNKNOWN',
        friendlyName: 'UNKNOWN',
      }
    }
  },
  /**
   * Handle the given photographer registration message.  The impact of photographer registration is the immediate
   * allocation of a 3 image allowance (up to) with a TTL of roughly 2 hours (may vary).
   * @param event The event declaring the photographer registration action.  Example event:
   * {
   *   "schema": "com.nordstrom/retail-stream/1-0-0",
   *   "origin": "hello-retail/photographer-registration-automation",
   *   "timeOrigin": "2017-01-12T18:29:25.171Z",
   *   "traceId": "1-6089c2ee-ee6f2517d06abc24fde41c4a",
   *   "data": {
   *     "schema": "com.nordstrom/user-info/update-phone/1-0-0",
   *     "id": "4579874",
   *     "phone": "1234567890"
   *   }
   * }
   * @param complete The callback with which to report any errors
   */
  registerPhotographer: (event, complete) => {
    // Submit XRay trace ID from previous trace due to lacking Kinesis support
    AWSXRay.captureFunc('annotations', function(subsegment) {
      subsegment.addAnnotation('root_trace_id', String(event.traceId));
    });
    const updated = Date.now()
    const putParams = {
      TableName: constants.TABLE_PHOTO_REGISTRATIONS_NAME,
      ConditionExpression: 'attribute_not_exists(id)',
      Item: {
        id: event.data.id,
        created: updated,
        createdBy: event.origin,
        updatedBy: event.origin,
        phone: event.data.phone,
        timeToLive: Math.ceil(updated / 1000 /* milliseconds per second */) + constants.TTL_DELTA_IN_SECONDS,
      },
    }
    dynamo.put(putParams, (err) => {
      if (err) {
        if (err.code && err.code === 'ConditionalCheckFailedException') {
          const updateParams = {
            TableName: constants.TABLE_PHOTO_REGISTRATIONS_NAME,
            Key: {
              id: event.data.id,
            },
            UpdateExpression: [
              'set',
              '#c=if_not_exists(#c,:c),',
              '#cb=if_not_exists(#cb,:cb),',
              '#u=:u,',
              '#ub=:ub,',
              '#tt=:tt',
            ].join(' '),
            ExpressionAttributeNames: {
              '#c': 'created',
              '#cb': 'createdBy',
              '#u': 'updated',
              '#ub': 'updatedBy',
              '#tt': 'timeToLive',
            },
            ExpressionAttributeValues: {
              ':c': updated,
              ':cb': event.origin,
              ':u': updated,
              ':ub': event.origin,
              ':tt': (Math.ceil(updated / 1000 /* milliseconds per second */) + constants.TTL_DELTA_IN_SECONDS).toString(),
            },
            ReturnValues: 'NONE',
            ReturnConsumedCapacity: 'NONE',
            ReturnItemCollectionMetrics: 'NONE',
          }
          dynamo.update(updateParams, complete)
        } else {
          console.log(`registerPhotographer error: ${err}`)
          complete(err)
        }
      } else {
        complete()
      }
    })
  },
  /**
   * Start and execution corresponding to the given event.  Swallow errors that result from attempting to
   * create the execution beyond the first time.
   * @param event The event to validate and process with the appropriate logic.  Example event:
   * {
   *   "schema": "com.nordstrom/retail-stream/1-0-0",
   *   "origin": "hello-retail/product-producer-automation",
   *   "timeOrigin": "2017-01-12T18:29:25.171Z",
   *   "traceId": "1-6089c2ee-ee6f2517d06abc24fde41c4a",
   *   "data": {
   *     "schema": "com.nordstrom/product/create/1-0-0",
   *     "id": "4579874",
   *     "brand": "POLO RALPH LAUREN",
   *     "name": "Polo Ralph Lauren 3-Pack Socks",
   *     "description": "PAGE:/s/polo-ralph-lauren-3-pack-socks/4579874",
   *     "category": "Socks for Men"
   *   }
   * }
   * @param complete The callback with which to report any errors
   */
  startExecution: (event, complete) => {
    // Submit XRay trace ID from previous trace due to lacking Kinesis support
    AWSXRay.captureFunc('annotations', function(subsegment) {
      subsegment.addAnnotation('root_trace_id', String(event.traceId));
    });
    const sfEvent = event
    sfEvent.merchantName = impl.eventSource(event.origin).friendlyName
    const params = {
      stateMachineArn: constants.STEP_FUNCTION,
      name: sfEvent.data.id,
      input: JSON.stringify(sfEvent),
    }
    stepfunctions.startExecution(params, (err) => {
      if (err) {
        if (err.code && err.code === 'ExecutionAlreadyExists') {
          complete()
        } else {
          console.log(`startExecution error: ${err}`)
          complete(err)
        }
      } else {
        complete()
      }
    })
  },
}

kh.registerSchemaMethodPair(updatePhoneSchema, impl.registerPhotographer)
kh.registerSchemaMethodPair(productCreateSchema, impl.startExecution)

module.exports = {
  processKinesisEvent: kh.processKinesisEvent.bind(kh),
}

// console.log(`${constants.MODULE} - CONST: ${JSON.stringify(constants, null, 2)}`)
// console.log(`${constants.MODULE} - ENV:   ${JSON.stringify(process.env, null, 2)}`)
