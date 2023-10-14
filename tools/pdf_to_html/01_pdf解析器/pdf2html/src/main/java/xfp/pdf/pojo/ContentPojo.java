package xfp.pdf.pojo;

import com.google.gson.annotations.Expose;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.apache.pdfbox.text.TextPosition;

import xfp.pdf.tools.RenderInfo;

import java.util.List;


@Data
@NoArgsConstructor
public class ContentPojo {
    public List<contentElement> outList;

    public ContentPojo(List<contentElement> outList){
        this.outList = outList;
    }
    //临时判断是否是ppt转成的pdf
    public Boolean isPptTransPDF;


    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class PdfStyleStruct{
        private String text;
        private Float lineWidth;
        private String renderingMode;
        private Integer rotation;
        private Float x;
        private Float y;
        private Float width;
        private Float height;

        private String fontName;
        private Float fontSize;
        private Float fontSizePt;
        private Float fontWeight;
        private String charSet;

        @Override
        public String toString() {
            return text;
        }
    }


    @Data
    @NoArgsConstructor
    public static class contentElement {
        Integer pageNumber;
        String elementType; //title,text,table,pic
        String level;
        Boolean titleStart;
        String titlePrefix;
        String titleBody;

        String path;
        String styleId;
        //word文档有些段落开头的自动编号,这个字段标明
        String autoNumber;

        //段落加粗情况0->未加粗，1->部分加粗，2->全部加粗
        Integer bold;

        String text;
        Integer row_num;
        Integer col_num;
        Float xStart;
        Float yStart;
        Float width;
        Float height;

        Float pageHeight;
        Float pageWidth;


        //如果本元素有跨页，这里存储其合并的其他Text
        List<contentElement> crossPageList;

//        public Text(Text t){
//            this.page_number = t.page_number;
//            this.element_type = t.element_type;
//            this.level = t.level;
//            this.titleStart = t.titleStart;
//            this.titlePrefix = t.titlePrefix;
//            this.titleBody = t.titleBody;
//            this.path = t.path;
//            this.styleId = t.styleId;
//            this.autoNumber = t.autoNumber;
//            this.bold = t.bold;
//            this.text = t.text;
//            this.row_num = t.row_num;
//            this.col_num = t.col_num;
//            this.xStart = t.xStart;
//            this.yStart = t.yStart;
//            this.width = t.width;
//            this.height = t.height;
//            this.pageHeight = t.pageHeight;
//            this.pageWidth =t.pageWidth;
//            this.crossPageList = new ArrayList<>(t.crossPageList);
//            this.startLine = new ArrayList<>(t.startLine);
//            this.startLineStatus = t.startLineStatus;
//            this.endLine = new ArrayList<>(t.endLine);
//            this.endLineStatus = t.endLineStatus;
//            this.wordStyleStructs = new ArrayList<>(wordStyleStructs);
//            this.pdfStyleStructs = new ArrayList<>(pdfStyleStructs);
//            this.msgStyleStructs = new ArrayList<>(msgStyleStructs);
//            this.cells = new ArrayList<>(cells);
//        }

        public void setText(String text) {
            if(text==null){
                return;
            }
            this.text = text;
        }

        /**
         * startLine和endLine是解析UntaggedPdf时，birdViewer需要用到的
         */
        @Expose(serialize = false, deserialize = false)
        List<Tu.Tuple2<TextPosition, RenderInfo>> startLine;
        @Expose(serialize = false, deserialize = false)
        LineStatus startLineStatus;
        @Expose(serialize = false, deserialize = false)
        List<Tu.Tuple2<TextPosition, RenderInfo>> endLine;
        @Expose(serialize = false, deserialize = false)
        LineStatus endLineStatus;

        //PDFStyleStruct
        List<PdfStyleStruct> pdfStyleStructs;

        List<InnerCell> cells;

        @Override
        public String toString() {
            return "Text{" +
                    "page_number=" + pageNumber +
                    ", element_type='" + elementType + '\'' +
                    ", level='" + level + '\'' +
                    ", text='" + text + '\'' +
                    ", row_num=" + row_num +
                    ", col_num=" + col_num +
                    ", cells=" + cells +
                    '}';
        }


        public contentElement(int pageNumber, String elementType, String text){
            this.pageNumber = pageNumber;
            this.elementType = elementType;
            this.text = text;
        }

        public contentElement(int pageNumber, String elementType, String level, String path, String text) {
            this.pageNumber = pageNumber;
            this.elementType = elementType;
            this.level = level;
            this.path = path;
            this.text = text;
        }

        public contentElement(int pageNumber, String elementType, int row_num,
                              int col_num, List<InnerCell> cells){
            this.pageNumber = pageNumber;
            this.elementType = elementType;
            this.row_num = row_num;
            this.col_num = col_num;
            this.cells = cells;
        }

        public contentElement(int pageNumber, String elementType, String level, String path, String text, Float xStart, Float yStart,
                              Float width, Float height){
            this.pageNumber = pageNumber;
            this.elementType = elementType;
            this.level = level;
            this.path = path;
            this.text = text;
            this.xStart = xStart;
            this.yStart = yStart;
            this.width = width;
            this.height = height;
        }

        public contentElement(int pageNumber, String elementType, String text, Float xStart, Float yStart,
                              Float width, Float height){
            this.pageNumber = pageNumber;
            this.elementType = elementType;
            this.text = text;
            this.xStart = xStart;
            this.yStart = yStart;
            this.width = width;
            this.height = height;
        }

        public contentElement(int pageNumber, String elementType, int row_num,
                              int col_num, List<InnerCell> cells, Float xStart, Float yStart,
                              Float width, Float height){
            this.pageNumber = pageNumber;
            this.elementType = elementType;
            this.row_num = row_num;
            this.col_num = col_num;
            this.cells = cells;
            this.xStart = xStart;
            this.yStart = yStart;
            this.width = width;
            this.height = height;
        }
        @Data
        public static class InnerCell{
            String text;
            Integer row_index;
            Integer col_index;
            Integer row_span;
            Integer col_span;

            //目前支持跨两页的表格合并，因此对pdf有必要有一个字段表示这个单元格在下一页
            Boolean isNextPage;
            Float xStart;
            Float yStart;
            Float width;
            Float height;

            public void setText(String text) {
                if(text==null){
                    return;
                }
                this.text = text;
            }



            public InnerCell(String text,Integer row_index,Integer col_index,
                             Integer row_span,Integer col_span){
                this.text = text;
                this.row_index = row_index;
                this.col_index = col_index;
                this.row_span = row_span;
                this.col_span = col_span;
            }

            public InnerCell() {

            }


            @Override
            public String toString() {
                return "InnerCell{" +
                        "text='" + text + '\'' +
                        ", row_index=" + row_index +
                        ", col_index=" + col_index +
                        ", row_span=" + row_span +
                        ", col_span=" + col_span +
                        '}';
            }
        }
    }
}
