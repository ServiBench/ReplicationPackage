# Thumbnail Generator - AWS Implementation

Implements the first use case on Amazon Web Services using Java and the serverless framework

## Building

Assuming Java 8 (JDK) and Apache Maven are installed just run the following command to compile the source code:

```bash
mvn clean install
```

## Deploying

Before deploying you might want to modify the names of the buckets in the `serverless.yml` to ensure they are unique:
```yaml
custom:
  image_bucket_name: <Name of the Input Bucket>
  thumb_bucket_name: <Name of the Output Bucket>
```

After the code has been built it can be deployed by running:

```bash
serverless deploy -v
```

## Destroying

To destroy the application you first have to make sure both buckets are empty. This process is not automated. To do this just open
the Web Interface and delete the contents of both the input and the output bucket. Removing the buckets themselves is not needed
since the Serverless Frameworks CloudFormation Script will handle this for us.

Another option to delete the contents of the buckets is by the help of the AWS CLI. To remove contents in the bucket
just run the following command for both buckets:

```bash
aws s3 rm s3://<S3_BUCKET_NAME> --recursive
```

To destroy the application just run:

```bash
serverless remove -v
```

## Usage

Every time a image gets uploaded to a S§ bucket the `thumbnail-generator` function triggers to generate
a Thumbnail of the uploaded image (i.e. a Image with the dimensions of 160x90 Pixels).
The thumbnail gets stored under the same key but in the thumbnail bucket defined in the `serverless.yml`.

A simple upload function is also deployed to simplify the upload

Sample command:

```bash
cat img.png | base64 -w0 | curl -H "Content-Type: image/png" -d @- "https://8afuw3tgc3.execute-api.us-east-1.amazonaws.com/dev/upload?filename=img.png"
```

Setting the filename is optional. If it is not set the function will compute the SHA256 hash of the uploaded image and use it as filename.

### Extract Invoke URL from Serverless

Currently just parsing the output log of `serverless deploy`:

```none
endpoints:
  POST - https://ab12c34def.execute-api.us-east-1.amazonaws.com/dev/upload
```

Alternatively, Use the [serverless-manifest-plugin](https://github.com/DavidWells/serverless-manifest-plugin) to create a nice JSON. Caveats: a) Needs to install plugin via extra `npm install` step in the build. b) Until the [PR#14](https://github.com/DavidWells/serverless-manifest-plugin/pull/14) is merged, the plugin crashes on deploy. A fix is available through `npm install --save medifle/serverless-manifest-plugin#cfd4b520243b52f378c751d6d1329e26643ebf8f`

## Testing

Testing can be done by uploading the images in the [test-images](../test-images) Directory using the command described above. 

To verify that the conversion has been executed you can use the following command of the AWS CLI:

```bash
aws s3 ls <Output Bucket Name>
```

To check if the upload was successful you can use the same command with the bucket name of the input bucket. The download of the images can be done by running the following command

```bash
aws s3 cp s3://<Output Bucket Name>/<Filename in Bucket> <Output Path on local Filesystem>
```
