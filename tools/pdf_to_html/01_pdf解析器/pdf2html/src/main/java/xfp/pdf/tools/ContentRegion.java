package xfp.pdf.tools;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.apache.pdfbox.text.TextPosition;
import org.apache.pdfbox.util.Matrix;

import java.util.List;


@Data
@NoArgsConstructor
@AllArgsConstructor
public class ContentRegion {
    public List<ContentLine> contentLines;
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ContentLine{
        private String line;
        private List<TextPosition> positions;
    }

    private static TextPosition textPositionForWordSep = new TextPosition(0, -2f, 0f, new Matrix(), 0f, 0f, 0f, 0f, 0f,
            "", null, null, 0f, 1);
    private static TextPosition textPositionForLineSep = new TextPosition(0, -1f, 0f, new Matrix(), 0f, 0f, 0f, 0f, 0f,
            "", null, null, 0f, 1);
    public static TextPosition createTextPositionForWordSep(){
        //为wwordSeparator创建的空TextPostion,特征是pageWidth等于-2f
        return textPositionForWordSep;
    }

    public static TextPosition createTextPositionForLineSep(){
        //为lineSeparator创建的空TextPostion,特征是pageWidth等于-2f
        return textPositionForLineSep;
    }
}
