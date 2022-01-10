package spblab.thumbgen.lambda;

@SuppressWarnings( {"unused", "WeakerAccess"})
public class Config {
    public static String[] VALID_MIME_TYPES = new String[] {"image/png", "image/jpeg"};
    public static String IMAGE_UPLOAD_BUCKET = System.getenv("IMAGE_UPLOAD_BUCKET");
    public static String THUMBNAIL_BUCKET = System.getenv("THUMBNAIL_BUCKET");
}
