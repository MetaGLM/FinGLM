package xfp.pdf.tools;

import lombok.Data;
import org.apache.pdfbox.pdmodel.graphics.state.RenderingMode;


@Data
public class RenderInfo {
    private Integer pageNum;
    private Float lineWidth;
    private RenderingMode renderingMode;

    @Override
    public String toString() {
        return "{" +
                "lineWidth=" + lineWidth +
                ", renderingMode=" + renderingMode +
                '}';
    }
}
