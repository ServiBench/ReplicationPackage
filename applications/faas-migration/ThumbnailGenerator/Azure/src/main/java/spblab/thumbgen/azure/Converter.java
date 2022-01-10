package spblab.thumbgen.azure;

import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;

import javax.imageio.ImageIO;

import org.imgscalr.Scalr;

public class Converter {

    public static byte[] createThumbnail(byte[] input) throws Exception {
        ByteArrayInputStream bin = new ByteArrayInputStream(input);
        BufferedImage img = ImageIO.read(bin);
        BufferedImage thumbnail = Scalr.resize(img, Scalr.Mode.FIT_TO_WIDTH, 160, 90);
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        ImageIO.write(thumbnail, "png", out);
        return out.toByteArray();
    }
}
