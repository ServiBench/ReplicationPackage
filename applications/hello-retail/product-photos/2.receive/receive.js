'use strict'

const AJV = require('ajv')
const AWSXRay = require('aws-xray-sdk-core') // eslint-disable-line import/no-unresolved, import/no-extraneous-dependencies
const aws = AWSXRay.captureAWS(require('aws-sdk')) // eslint-disable-line import/no-unresolved, import/no-extraneous-dependencies
const BbPromise = require('bluebird')
const got = require('got')
const https = require('https')

/**
 * AJV
 */
const photoInputSchema = require('./photo-input-schema.json')
const photoAssignmentSchema = require('./photo-assignment-schema.json')

const makeSchemaId = schema => `${schema.self.vendor}/${schema.self.name}/${schema.self.version}`

const photoInputSchemaId = makeSchemaId(photoInputSchema)
const photoAssignmentSchemaId = makeSchemaId(photoAssignmentSchema)


const ajv = new AJV()
ajv.addSchema(photoInputSchema, photoInputSchemaId)
ajv.addSchema(photoAssignmentSchema, photoAssignmentSchemaId)

/**
 * AWS
 */
aws.config.setPromisesDependency(BbPromise)
const dynamo = new aws.DynamoDB.DocumentClient()
const s3 = new aws.S3()
const stepfunctions = new aws.StepFunctions()

/**
 * Constants
 */
const constants = {
  // Errors
  ERROR_CLIENT: 'ClientError',
  ERROR_UNAUTHORIZED: 'Unauthorized',
  ERROR_USER: 'UserError',
  ERROR_SERVER: 'ServerError',
  ERROR_DATA_CORRUPTION: 'DATA CORRUPTION',
  ERROR_SECURITY_RISK: '!!!SECURITY RISK!!!',
  HASHES: '##########################################################################################',

  // Locations
  MODULE: 'receive.js',
  METHOD_HANDLER: 'handler',
  METHOD_PLACE_IMAGE_IN_S3: 'impl.storeImage',
  METHOD_SEND_STEP_SUCCESS: 'impl.sendStepSuccess',

  // External
  ENDPOINT: process.env.ENDPOINT,
  IMAGE_BUCKET: process.env.IMAGE_BUCKET,
  TABLE_PHOTO_ASSIGNMENTS_NAME: process.env.TABLE_PHOTO_ASSIGNMENTS_NAME,
}

/**
 * Errors
 */
class ClientError extends Error {
  constructor(message) {
    super(message)
    this.name = constants.ERROR_CLIENT
  }
}
class AuthError extends Error {
  constructor(message) {
    super(message)
    this.name = constants.ERROR_UNAUTHORIZED
  }
}
class UserError extends Error {
  constructor(message) {
    super(message)
    this.name = constants.ERROR_USER
  }
}
class ServerError extends Error {
  constructor(message) {
    super(message)
    this.name = constants.ERROR_SERVER
  }
}

/**
 * Utility Methods (Internal)
 */
const util = {
  response: (statusCode, body) => ({
    statusCode,
    headers: {
      'Access-Control-Allow-Origin': '*', // Required for CORS support to work
      'Access-Control-Allow-Credentials': true, // Required for cookies, authorization headers with HTTPS
    },
    body,
  }),
}

/**
 * Implementation (Internal)
 */
const impl = {
  /**
   * Validate the request.
   * @param event The event representing the HTTPS POST request
   * {
   *   photographer: {
   *     id: 'PHOTOGRAPHER ID',
   *     phone: 'PHONE NUMBER'
   *   },
   *   For:  'ITEM ID',
   *   Media: '...' base64 encoded jpeg image
   * }
   */
  validateRequest: (event) => {
    const body = JSON.parse(event.body)
    if (!body.For) {
      return BbPromise.reject(new UserError('Request did not contain the Item ID the photo is for'))
    } else if (!body.photographer.id) {
      return BbPromise.reject(new ServerError('Request did not contain the photographer id the image came from.'))
    } else if (!body.photographer.phone) {
      return BbPromise.reject(new ServerError('Request did not contain the phone number the image came from.'))
    } else if (!body.Media) {
      return BbPromise.reject(new ServerError('Request did not contain the image.'))
    } else {
      return BbPromise.resolve({
        event,
        body,
      })
    }
  },
  getResources: results => BbPromise.all([
    impl.getImage(results),
    impl.getAssignment(results),
  ]),
  /**
   * Download image from URI in HTTPS request.
   * @param results The event representing the HTTPS request
   */
  getImage: (results) => {
    return BbPromise.resolve({
        contentType: 'image/jpeg',
        contentEncoding : 'base64',
        data: results.body.Media,
      })
  },
  /**
   * Obtain the assignment associated with the number/ID that this message/image is being received from.
   * @param results The event representing the HTTPS request
   */
  getAssignment: (results) => {
    const params = {
      Key: {
        id: results.body.For,
      },
      TableName: constants.TABLE_PHOTO_ASSIGNMENTS_NAME,
      AttributesToGet: [
        'taskToken',
        'taskEvent',
      ],
      ConsistentRead: false,
      ReturnConsumedCapacity: 'NONE',
    }
    return dynamo.get(params).promise()
      .then(
        (data) => {
          if (!data.Item) {
            return BbPromise.reject(new UserError('Oops!  We couldn\'t find your assignment.  If you have registered and not completed your assignments, we will send one shortly.'))
          } else {
            const item = data.Item
            item.taskEvent = JSON.parse(item.taskEvent)
            item.taskEvent.photographer = results.body.photographer
            return BbPromise.resolve(item)
          }
        },
        ex => BbPromise.reject(new ServerError(`Failed to retrieve assignment: ${ex}`)) // eslint-disable-line comma-dangle
      )
  },
  /**
   * Using the results of the `getImage` and `getAssignment` invocations, place the obtained image into the
   * proper location of the bucket for use in the web UI.
   * @param results An array of results obtained from `getResources`.  Details:
   *          results[0] = image       // The user's image that was downloaded
   *          results[1] = assignment  // The assignment associated with the given request's phone number/ID
   */
  storeImage: (results) => {
    const image = results[0]
    const assignment = results[1]

    const bucketKey = `i/p/${assignment.taskEvent.data.id}`

    const params = {
      Bucket: constants.IMAGE_BUCKET,
      Key: bucketKey,
      Body: image.data,
      ContentType: image.contentType,
      ContentEncoding : image.contentEncoding,
      Metadata: {
        from: assignment.taskEvent.photographer.phone,
      },
    }
    return s3.putObject(params).promise().then(
      () => BbPromise.resolve({
        assignment,
        image: `${constants.IMAGE_BUCKET}/${bucketKey}`, // TODO this assumes parity between bucket name and website URI
      }),
      ex => BbPromise.reject(new ServerError(`Error placing image into S3: ${ex}`)) // eslint-disable-line comma-dangle
    )
  },
  /**
   * Indicate the successful completion of the photographer's image assignment to the StepFunction
   * @param results The results of the placeImage, containing the assignment and new image location
   */
  sendStepSuccess: (results) => {
    const taskEvent = results.assignment.taskEvent
    taskEvent.image = results.image
    taskEvent.success = 'true'
    const params = {
      output: JSON.stringify(taskEvent),
      taskToken: results.assignment.taskToken,
    }
    return stepfunctions.sendTaskSuccess(params).promise().then(
      () => BbPromise.resolve(taskEvent),
      err => BbPromise.reject(new ServerError(`Error sending success to Step Function: ${err}`)) // eslint-disable-line comma-dangle
    )
  },
  userErrorResp: (error) => {
    return error.message
  },
  thankYouForImage: (taskEvent) => {
    return `Thanks so much ${taskEvent.photographer.id}!`
  },
}
/**
 * API (External)
 */
module.exports = {
  handler: (event, context, callback) => {
    impl.validateRequest(event)
      .then(impl.getResources)
      .then(impl.storeImage)
      .then(impl.sendStepSuccess)
      .then(impl.thankYouForImage)
      .then((msg) => {
        const response = util.response(200, msg)
        response.headers['Content-Type'] = 'text/xml'
        callback(null, response)
      })
      .catch(ClientError, (ex) => {
        console.log(`${constants.MODULE} - ${ex.stack}`)
        callback(null, util.response(400, `${ex.name}: ${ex.message}`))
      })
      .catch(AuthError, (ex) => {
        console.log(`${constants.MODULE} - ${ex.stack}`)
        callback(null, util.response(403, constants.ERROR_UNAUTHORIZED))
      })
      .catch(UserError, (ex) => {
        console.log(`${constants.MODULE} - ${ex.stack}`)
        const response = util.response(200, impl.userErrorResp(ex))
        response.headers['Content-Type'] = 'text/xml'
        callback(null, response)
      })
      .catch(ServerError, (ex) => {
        console.log(`${constants.MODULE} - ${ex.stack}`)
        callback(null, util.response(500, ex.name))
      })
      .catch((ex) => {
        console.log(`${constants.MODULE} - Uncaught exception: ${ex.stack}`)
        callback(null, util.response(500, constants.ERROR_SERVER))
      })
  },
}
