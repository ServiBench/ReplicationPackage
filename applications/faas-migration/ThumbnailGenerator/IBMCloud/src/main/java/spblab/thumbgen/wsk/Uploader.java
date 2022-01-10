package spblab.thumbgen.wsk;

import java.io.ByteArrayInputStream;
import java.io.CharArrayWriter;
import java.io.PrintWriter;

import com.google.api.client.util.Base64;
import com.google.gson.JsonObject;
import io.minio.MinioClient;

@SuppressWarnings("DuplicatedCode")
public class Uploader {
    public static JsonObject main(JsonObject args) {
        System.out.println(args.toString());
        byte[] contents = null;
        String filename = null;
        // Check input parameters
        if (!args.has("filename")) {
            JsonObject response = new JsonObject();
            response.addProperty("status", "fail");
            response.addProperty("message", "Parameter \"filename\" is required!");
            return response;
        }
        filename = args.get("filename").getAsString();
        if (!args.has("data")) {
            JsonObject response = new JsonObject();
            response.addProperty("status", "fail");
            response.addProperty("message", "Parameter \"data\" is required!");
            return response;
        } else {
            try {
                // Decode input data
                contents = Base64.decodeBase64(args.get("data").getAsString());
            } catch (Exception e) {
                // If the decode fails return a error
                JsonObject response = new JsonObject();
                response.addProperty("status", "fail");
                response.addProperty("message", "Parameter \"data\" must be Base64 Encoded!");
                return response;
            }
        }
        try {
            // Parse parameters
            String endpoint = args.get("endpoint").getAsString();
            String accessKey = args.get("access_key").getAsString();
            String secretKey = args.get("secret_key").getAsString();
            String bucketName = args.get("bucket").getAsString();
            System.out.printf("E: %s A: %s S: %s\n", endpoint, accessKey, secretKey);
            MinioClient client = new MinioClient(endpoint, accessKey, secretKey);

            // Check if output bucket is present
            // Probably not needed. Created from experience when implementing the matirx multiplication use case
            // There it was necessary to avoid an exception
            if (!client.bucketExists(bucketName)) {
                System.out.println("Creating Bucket");
                client.makeBucket(bucketName);
            }

            // Store the Image in object Storage
            client.putObject(bucketName, filename, new ByteArrayInputStream(contents), (long) contents.length, null, null, null);
        } catch (Exception e) {
            // If something goes wrong return a error message including stacktrace
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
        // Return sucess message
        JsonObject response = new JsonObject();
        response.addProperty("status", "ok");
        return response;
    }
}
