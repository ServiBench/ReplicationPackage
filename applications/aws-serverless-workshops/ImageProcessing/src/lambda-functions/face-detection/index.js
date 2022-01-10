const util = require('util');
const AWSXRay = require('aws-xray-sdk-core');
AWSXRay.middleware.setSamplingRules('no-sampling.json');
const AWS = AWSXRay.captureAWS(require('aws-sdk'));
const rekognition = new AWS.Rekognition();

exports.handler = (event, context, callback) =>
{

    const srcBucket = event.s3Bucket;
    // Object key may have spaces or unicode non-ASCII characters.
    const srcKey = decodeURIComponent(event.s3Key.replace(/\+/g, " "));

    var params = {
        Image: {
            S3Object: {
                Bucket: srcBucket,
                Name: srcKey
            }
        },
        Attributes: ['ALL']
    };

    // Limits: https://docs.aws.amazon.com/rekognition/latest/dg/limits.html
    // Service quota: https://docs.aws.amazon.com/general/latest/gr/rekognition.html#limits_rekognition
    // Often 5rps in many regions but 50rps in us-east-1 (2021-04-27)
    // For spiky traffic, AWS recommends smoothing mechanisms such as queuing architecture
    // demonstrated here: https://github.com/aws-samples/amazon-rekognition-serverless-large-scale-image-and-video-processing
    rekognition.detectFaces(params).promise().then((data)=> {
        if (data.FaceDetails.length != 1) {
            callback(new PhotoDoesNotMeetRequirementError("Detected " + data.FaceDetails.length + " faces in the photo."));
        } else {
            if (data.FaceDetails[0].Sunglasses.Value === true){
                callback(new PhotoDoesNotMeetRequirementError("Face is wearing sunglasses"));
            }
            var detectedFaceDetails = data.FaceDetails[0];
            // remove some fields not used in further processing to de-clutter the output.
            delete detectedFaceDetails['Landmarks'];
            callback(null, detectedFaceDetails);
        }
    }).catch( err=> {
        console.log(err);
        if (err.code === "ImageTooLargeException"){
            callback(new PhotoDoesNotMeetRequirementError(err.message));
        }
        if (err.code === "InvalidImageFormatException"){
            callback(new PhotoDoesNotMeetRequirementError("Unsupported image file format. Only JPEG or PNG is supported"));
        }
        callback(err);
    });
};


function PhotoDoesNotMeetRequirementError(message) {
    this.name = "PhotoDoesNotMeetRequirementError";
    this.message = message;
}
PhotoDoesNotMeetRequirementError.prototype = new Error();
