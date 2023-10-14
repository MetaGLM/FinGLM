package xfp.pdf.tools;

import com.google.gson.ExclusionStrategy;
import com.google.gson.FieldAttributes;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import org.apache.commons.lang.StringEscapeUtils;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.text.PDFTextStripperByArea;
import org.apache.pdfbox.text.TextPosition;
import xfp.pdf.pojo.Tu;


import java.awt.geom.Rectangle2D;
import java.io.IOException;
import java.text.DecimalFormat;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public class TextTool {

    /**
     * 替换字符串&为和，这是因为&在dom4j中属于特殊字符，会影响解析dom
     * @param str 输入字符串
     * @return 返回替换后的字符串
     */
    public static String reKeyAnd(String str){
        if(str==null){
            return "";
        }
        return str.replaceAll("&","和");
    }
    /**
     * 反向替换
     * @param str 输入字符串
     * @return 返回替换后的字符串
     */
    public static String bakKeyAnd(String str){
        if(str==null){
            return "";
        }
        return str.replaceAll("和","&");
    }

    /**
     * 返回json str
     * @param object 对象
     * @return json str
     */
    public static String toJson(Object object) {
        Gson gson = new GsonBuilder().disableHtmlEscaping().setPrettyPrinting().addSerializationExclusionStrategy(new ExclusionStrategy() {
            @Override
            public boolean shouldSkipField(FieldAttributes fa) {
                return fa.getName().equals("startLine") || fa.getName().equals("startLineStatus") ||
                        fa.getName().equals("endLine") || fa.getName().equals("endLineStatus")
                        ||fa.getName().equals("WordStyleStruct")
                        || fa.getName().equals("pdfStyleStructs")  || fa.getName().equals("trueColIndex")
                        ||fa.getName().equals("vMerge");
            }

            @Override
            public boolean shouldSkipClass(Class<?> arg0) {
                // TODO Auto-generated method stub
                return false;
            }
        }).create();
        return gson.toJson(object);
    }

    /**
     * 将escape过的str转换回来
     * @param str 输入字符串
     * @return 输出字符串
     */
    public static String unescape(String str){
        return StringEscapeUtils.unescapeHtml(str);
    }

    /**
     * 将str被escape
     * @param str 输入字符串
     * @return 输出字符串
     */
    public static String escape(String str){
        return StringEscapeUtils.escapeHtml(str);
    }

    /**
     * 将文本及其位置信息封装入String
     * @param text 文本内容
     * @param xStart 文本x起始位置
     * @param yStart 文本y起始位置
     * @param xEnd 文本x结束位置
     * @param yEnd 文本y结束位置
     * @return 含有文本内容及位置信息的String
     */
    public static String encodeTextLine(String text,float xStart,float yStart,float xEnd,float yEnd){
        DecimalFormat decimalFormat = new DecimalFormat("000.000");
        String xStartStr = decimalFormat.format(xStart);
        String yStartStr = decimalFormat.format(yStart);
        String xEndStr = decimalFormat.format(xEnd);
        String yEndStr = decimalFormat.format(yEnd);
        return xStartStr+yStartStr+xEndStr+yEndStr+text;
    }

    /**
     * 将文本内容和位置信息拆分开来
     * @param line 文本内容及位置信息
     * @return 拆分后的数组
     */
    public static String[] decodeTextLine(String line){
        String xStart = line.substring(0, 7);
        String yStart = line.substring(7, 14);
        String xEnd = line.substring(14, 21);
        String yEnd = line.substring(21, 28);
        String text = line.substring(28, line.length());
        return new String[]{text,xStart,yStart,xEnd,yEnd};
    }


    public static List<Tu.Tuple2<String,Rectangle2D>> grabText(PDDocument pd, List<Rectangle2D> ranges, int pageNum) throws IOException {
        List<Tu.Tuple2<String,Rectangle2D>> result = new ArrayList<>();
        PDFTextStripperByArea stripper = new PDFTextStripperByArea();
        int count = 0;
        for(Rectangle2D rect:ranges){
            stripper.addRegion(count+"",rect);
            count++;
        }

        PDPage docPage = pd.getPage(pageNum-1);

        stripper.extractRegions(docPage);

        for(int i=0;i<count;i++){
            String textForRegion = stripper.getTextForRegion(i+"");
            Rectangle2D rectangle2D = ranges.get(i);

            result.add(new Tu.Tuple2<>(textForRegion,rectangle2D));
        }
        return result;
    }


    public static List<Tu.Tuple3<List<List<Tu.Tuple2<TextPosition, RenderInfo>>>,String,Rectangle2D>> grabTextEnhance(PDDocument pd, List<Tu.Tuple2<Boolean,Rectangle2D>> ranges,int pageNum) throws IOException {
        List<Tu.Tuple3<List<List<Tu.Tuple2<TextPosition, RenderInfo>>>,String,Rectangle2D>> result = new ArrayList<>();

        ModifiedPDFTextStripperByArea stripper = new ModifiedPDFTextStripperByArea();
        int count = 0;


        for(Tu.Tuple2<Boolean,Rectangle2D> tu:ranges){
            stripper.addRegion(count+"",tu.getValue());
            count++;
        }

        PDPage docPage = pd.getPage(pageNum-1);
        PDRectangle cropBox = docPage.getCropBox();
        stripper.extractRegions(docPage);

        for(int i=0;i<count;i++){
            Tu.Tuple2<Boolean, Rectangle2D> tu = ranges.get(i);
            Boolean key = tu.getKey();
            Tu.Tuple3<List<List<Tu.Tuple2<TextPosition, RenderInfo>>>,String,Rectangle2D> newTu = new Tu.Tuple3<>();
            if(key){
                //需要获得详细内容
                List<List<Tu.Tuple2<TextPosition, RenderInfo>>> detailedTextForRange = stripper.getDetailedTextForRange(i + "");
                newTu.setValue1(detailedTextForRange);
            }else{
                String textForRegion = stripper.getTextForRegion(i+"");
                newTu.setValue2(textForRegion);
            }
            newTu.setValue3(ranges.get(i).getValue());
            result.add(newTu);
        }
        return result;
    }

    public static boolean isContainChinese(String str){
        String reg = "[\\u4E00-\\u9FA5]+";
        Pattern p = Pattern.compile(reg);
        Matcher m = p.matcher(str);
        if(m.find()){
            return true;
        }else{
            return false;
        }
    }


    public static boolean isContainEnglish(String str){
        String reg = "[A-Za-z]";
        Pattern p = Pattern.compile(reg);
        Matcher m = p.matcher(str);
        if(m.find()){
            return true;
        }else{
            return false;
        }
    }


}
