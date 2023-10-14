package xfp.pdf.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.apache.pdfbox.text.TextPosition;
import xfp.pdf.tools.RenderInfo;


import java.util.List;


@Data
@NoArgsConstructor
@AllArgsConstructor
public class TextBlock {
    //外层list，行，内层list 每行的每个字
    private List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region;
    //id是region的标识
    private Integer id;
}
