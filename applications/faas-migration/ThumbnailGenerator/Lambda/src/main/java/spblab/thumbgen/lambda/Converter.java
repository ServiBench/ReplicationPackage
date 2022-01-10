package spblab.thumbgen.lambda;

import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.RenderingHints;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.imageio.ImageIO;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

public class Converter {
    private static final Logger LOG = LogManager.getLogger(Converter.class);

    private static final float MAX_WIDTH = 160;
    private static final float MAX_HEIGHT = 90;
    private final String JPG_TYPE = "jpg";
    private final String JPG_MIME = "image/jpeg";
    private final String PNG_TYPE = "png";
    private final String PNG_MIME = "image/png";

    private final boolean typeInferable;
    private final String fileType;

    public Converter(String srcKey) {
        Matcher matcher = Pattern.compile(".*\\.([^.]*)").matcher(srcKey);
        this.typeInferable = matcher.matches();
        if (typeInferable) {
            this.fileType = matcher.group(1);
        } else {
            this.fileType = "";
        }
    }

    public ByteArrayOutputStream createThumbnail(InputStream objectData) throws IOException {
        BufferedImage srcImage = ImageIO.read(objectData);
        int srcHeight = srcImage.getHeight();
        int srcWidth = srcImage.getWidth();

        float scalingFactor = Math.min(MAX_WIDTH / srcWidth, MAX_HEIGHT / srcHeight);
        int width = (int) (scalingFactor * srcWidth);
        int height = (int) (scalingFactor * srcHeight);

        BufferedImage resizedImage = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = resizedImage.createGraphics();
        // Fill with white before applying semi-transparent (alpha) images
        g.setPaint(Color.white);
        g.fillRect(0, 0, width, height);
        // Simple bilinear resize
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        g.drawImage(srcImage, 0, 0, width, height, null);
        g.dispose();

        // Re-encode image to target format
        ByteArrayOutputStream os = new ByteArrayOutputStream();
        ImageIO.write(resizedImage, fileType, os);

        return os;
    }

    public boolean isTypeInferable() {
        return this.typeInferable;
    }

    public boolean isImage() {
        return JPG_TYPE.equals(fileType) || PNG_TYPE.equals(fileType);
    }

    public String getImageMimeType() {
        if (JPG_TYPE.equals(fileType)) {
            return JPG_MIME;
        } else if (PNG_TYPE.equals(fileType)) {
            return PNG_MIME;
        }
        return "";
    }
}
