package spblab.thumbgen.wsk;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.CharArrayWriter;
import java.io.InputStream;
import java.io.PrintWriter;

import com.google.api.client.util.IOUtils;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import io.minio.MinioClient;
import spblab.thumbgen.wsk.model.ObjectStorageEvent;

@SuppressWarnings("DuplicatedCode")
public class Generator {
    public static JsonObject main(JsonObject args) {
        System.out.println(args.toString());
        Gson gson = new Gson();
        ObjectStorageEvent evt = gson.fromJson(args, ObjectStorageEvent.class);
        // Cancel execution if the event type does not match a insert event
        // This is necessary because the experimental implementation
        // triggers the action everytime something happens in the object storage
        // Since we only want to act upon insertion events all others will end here.
        if (!evt.getStatus().equals("added")) {
            System.out.println("Skipping event because the object is not added into the Bucket.");
            JsonObject response = new JsonObject();
            response.addProperty("status", "skipped");
            return response;
        }

        try {
            // Parse Parameters
            String endpoint = args.get("endpoint").getAsString();
            String accessKey = args.get("access_key").getAsString();
            String secretKey = args.get("secret_key").getAsString();
            String bucketName = args.get("output_bucket").getAsString();
            System.out.printf("E: %s A: %s S: %s\n", endpoint, accessKey, secretKey);

            // Connect To S3
            MinioClient client = new MinioClient(endpoint, accessKey, secretKey);

            // Check if bucket exists
            if (!client.bucketExists(bucketName)) {
                System.out.println("Creating Bucket");
                client.makeBucket(bucketName);
            }
            // Download image into memory
            String inputBucket = evt.getBucket();
            InputStream in = client.getObject(inputBucket, evt.getFile().getKey());
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            IOUtils.copy(in, out);
            in.close();

            // Generate Thumbnail
            byte[] convertedImage = Converter.createThumbnail(out.toByteArray());

            // Upload result
            ByteArrayInputStream bin = new ByteArrayInputStream(convertedImage);
            client.putObject(bucketName, evt.getFile().getKey(), bin, (long) convertedImage.length, null, null, null);
        } catch (Exception e) {
            // return error with stacktrace if something goes wrong
            CharArrayWriter out = new CharArrayWriter();
            e.printStackTrace(new PrintWriter(out));
            e.printStackTrace(System.out);

            JsonObject response = new JsonObject();
            response.addProperty("status", "fail");
            response.addProperty("exception", e.getClass().getName());
            response.addProperty("message", e.getMessage());
            response.addProperty("stack_trace", new String(out.toCharArray()));
            return response;
        }

        // Return success message
        JsonObject response = new JsonObject();
        response.addProperty("status", "ok");
        return response;
    }
}
