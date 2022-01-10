package spblab.thumbgen.azure;

import java.util.Base64;
import java.util.logging.Logger;

import com.microsoft.azure.functions.ExecutionContext;
import com.microsoft.azure.functions.HttpMethod;
import com.microsoft.azure.functions.HttpRequestMessage;
import com.microsoft.azure.functions.HttpResponseMessage;
import com.microsoft.azure.functions.HttpStatus;
import com.microsoft.azure.functions.OutputBinding;
import com.microsoft.azure.functions.annotation.AuthorizationLevel;
import com.microsoft.azure.functions.annotation.BindingName;
import com.microsoft.azure.functions.annotation.BlobOutput;
import com.microsoft.azure.functions.annotation.BlobTrigger;
import com.microsoft.azure.functions.annotation.FunctionName;
import com.microsoft.azure.functions.annotation.HttpTrigger;
import com.microsoft.azure.functions.annotation.StorageAccount;

@SuppressWarnings("Duplicates")
public class ThumbnailGenerator {

    @FunctionName("Create-Thumbnail")
    @StorageAccount(Config.STORAGE_ACCOUNT_NAME)
    @BlobOutput(name = "$return", path = "output/{name}")
    public byte[] generateThumbnail(
            @BlobTrigger(name = "blob", path = "input/{name}")
                    byte[] content,
            final ExecutionContext context
    ) {
        try {
            return Converter.createThumbnail(content);
        } catch (Exception e) {
            e.printStackTrace();
            return content;
        }
    }

    @FunctionName("Upload-Image")
    @StorageAccount(Config.STORAGE_ACCOUNT_NAME)
    public HttpResponseMessage upload(
            @HttpTrigger(name = "req", methods = {HttpMethod.POST}, authLevel = AuthorizationLevel.ANONYMOUS)
                    HttpRequestMessage<String> request,
            @BindingName("name") String fileName,
            @BlobOutput(name = "out", path = "input/{name}")
                    OutputBinding<byte[]> blobOutput,
            final ExecutionContext context
    ) {
        Logger log = context.getLogger();
        log.info(fileName);
        log.info("" + request.getBody().length());

        byte[] data = Base64.getDecoder().decode(request.getBody());

        blobOutput.setValue(data);
        return request.createResponseBuilder(HttpStatus.OK).build();
    }
}
