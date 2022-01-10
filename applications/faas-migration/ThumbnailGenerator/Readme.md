# Thumbnail Generator

The thumbnail generator is intended to create a Thumbnail of an Image everytime an image is uploaded to Object storage.

## Testing

The [test-images](test-images/) directory contains two different images as well as the expected thumbnails. Since the conversion algorithm is deterministic this can be used as a reference point to validate the operation of a deployed instance. Instructions on how to submit and retrieve these images can be found in the Implementation specific readmes.

## Specification

Because the AWS and Azure approach of uploading a Base64 encoded image as the Request body does not work on IBM Cloud we have decided to not specify the way the upload function should behave.
