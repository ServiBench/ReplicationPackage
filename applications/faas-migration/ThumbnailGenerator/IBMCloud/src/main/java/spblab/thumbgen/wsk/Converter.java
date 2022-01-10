package spblab.thumbgen.wsk;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;

import javax.imageio.ImageIO;

import org.imgscalr.Scalr;

public class Converter {

    /**
     Creates a Thumbnail from the given input.
     If the operation fails a Exception is thrown, otherwise the thumbnail encoded as Byte Array is returned
     */
    public static byte[] createThumbnail(byte[] input) throws Exception {
        ByteArrayInputStream bin = new ByteArrayInputStream(input);
        BufferedImage img = ImageIO.read(bin);
        BufferedImage thumbnail = Scalr.resize(img, Scalr.Mode.FIT_TO_WIDTH, 160, 90);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ImageIO.write(thumbnail, "png", out);
        return out.toByteArray();
    }
}