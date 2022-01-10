package spblab.thumbgen.lambda;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;

import com.amazonaws.AmazonServiceException;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.S3Event;
import com.amazonaws.services.s3.AmazonS3;
import com.amazonaws.services.s3.AmazonS3ClientBuilder;
import com.amazonaws.services.s3.event.S3EventNotification;
import com.amazonaws.services.s3.model.GetObjectRequest;
import com.amazonaws.services.s3.model.ObjectMetadata;
import com.amazonaws.services.s3.model.S3Object;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import static spblab.thumbgen.lambda.Config.THUMBNAIL_BUCKET;

public class ThumbnailGenerationHandler implements RequestHandler<S3Event, String> {
    private static final Logger LOG = LogManager.getLogger(ThumbnailGenerationHandler.class);

    @Override
    public String handleRequest(S3Event input, Context context) {
        StringBuilder bout = new StringBuilder();

        S3EventNotification.S3EventNotificationRecord record = input.getRecords().get(0);

        String srcBucket = record.getS3().getBucket().getName();
        String srcKey = record.getS3().getObject().getUrlDecodedKey();
        String dstKey = "resized-" + srcKey;
        LOG.info("Loading {}/{}", srcBucket, srcKey);

        Converter c = new Converter(srcKey);
        if (!c.isTypeInferable()) {
            LOG.info("Unable to infer image type for key " + srcKey);
            return "No thumbnail for you!";
        }
        if (!c.isImage()) {
            LOG.info("Skipping non-image " + srcKey);
            return "No thumbnail for you!";
        }

        try {
            LOG.info("Starting thumbnail generation process");
            AmazonS3 s3Client = AmazonS3ClientBuilder.defaultClient();
            S3Object s3Object = s3Client.getObject(new GetObjectRequest(srcBucket, srcKey));
            InputStream objectData = s3Object.getObjectContent();
            ByteArrayOutputStream os = c.createThumbnail(objectData);

            InputStream convertedImage = new ByteArrayInputStream(os.toByteArray());
            // Set Content-Length and Content-Type
            ObjectMetadata meta = new ObjectMetadata();
            meta.setContentLength(os.size());
            meta.setContentType(c.getImageMimeType());

            LOG.info("Writing the thumbnail to: " + THUMBNAIL_BUCKET + "/" + dstKey);
            s3Client.putObject(THUMBNAIL_BUCKET, dstKey, convertedImage, meta);

            LOG.info("Successfully resized " + srcBucket + "/" + srcKey + " and uploaded to " + THUMBNAIL_BUCKET + "/" + dstKey);
            return "Ok";
        } catch (IOException | AmazonServiceException e) {
            e.printStackTrace();
            LOG.error("Thumbnail generation failed: {}", e.getMessage());
            System.exit(1);
        }
        LOG.info("Thumbnail generation is finished!");

        return "Done!";
    }
}
