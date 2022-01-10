package spblab.thumbgen.lambda;

import java.io.ByteArrayInputStream;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayProxyRequestEvent;
import com.amazonaws.services.s3.AmazonS3Client;
import com.amazonaws.services.s3.model.ObjectMetadata;
import com.amazonaws.services.s3.model.PutObjectResult;
import com.amazonaws.util.Base64;
import org.apache.commons.codec.binary.Hex;
import org.apache.commons.codec.digest.DigestUtils;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import spblab.thumbgen.lambda.utils.ApiGatewayResponse;

import static spblab.thumbgen.lambda.Config.IMAGE_UPLOAD_BUCKET;
import static spblab.thumbgen.lambda.Config.VALID_MIME_TYPES;

@SuppressWarnings("unused")
public class UploadHandler implements RequestHandler<APIGatewayProxyRequestEvent, ApiGatewayResponse> {
    private static final Logger LOG = LogManager.getLogger(UploadHandler.class);
    private AmazonS3Client client = new AmazonS3Client();

    @Override
    public ApiGatewayResponse handleRequest(APIGatewayProxyRequestEvent input, Context context) {
        String mimeType = input.getHeaders().getOrDefault("Content-Type", "unset");
        boolean hasFilename = false;
        String filename = "";
        if (input.getQueryStringParameters().containsKey("filename")) {
            hasFilename = true;
            filename = input.getQueryStringParameters().get("filename");
        }
        if (mimeType.equals("unset")) {
            mimeType = input.getHeaders().getOrDefault("content-type", "unset");
        }
        if (!Arrays.asList(VALID_MIME_TYPES).contains(mimeType)) {
            return respond(400, "Invalid Mime Type");
        }
        if (input.getBody().length() == 0) {
            return respond(400, "Body must not be Empty");
        }
        byte[] body = null;
        try {
            body = Base64.decode(input.getBody());
        } catch (Exception e) {
            e.printStackTrace();
            LOG.error(e);
            return respond(400, "Body must be Encoded in Base64");
        }

        if (!hasFilename) {
            filename = Hex.encodeHexString(DigestUtils.digest(DigestUtils.getSha256Digest(), body));
        }

        ByteArrayInputStream in = new ByteArrayInputStream(body);

        PutObjectResult response = client.putObject(IMAGE_UPLOAD_BUCKET, filename, in, new ObjectMetadata());

        return respond(200, filename);
    }

    private ApiGatewayResponse respond(int code, String message) {
        return respond(code, message, new HashMap<>());
    }

    private ApiGatewayResponse respond(int code, String message, Map<String, Object> additional) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("code", code);
        payload.put("message", message);
        additional.forEach(payload::put);
        return ApiGatewayResponse.builder()
                .setStatusCode(code)
                .setObjectBody(payload)
                .build();
    }
}
