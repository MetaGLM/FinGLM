package xfp.pdf.core;

import lombok.Data;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.TextPosition;


import xfp.pdf.pojo.Language;
import xfp.pdf.pojo.TextBlock;
import xfp.pdf.pojo.Tu;
import xfp.pdf.table.CellAnalyser;
import xfp.pdf.tools.RenderInfo;
import xfp.pdf.tools.TextTool;

import java.awt.*;
import java.awt.geom.Rectangle2D;
import java.io.IOException;
import java.util.List;
import java.util.*;

@Data
public class UnTaggedContext {
    private PDDocument document;

    private Language language;

    /**
     * 机器学习构建数据集用
     */
    private StringBuilder sb = new StringBuilder();

    //页面的最左侧位置和最右侧位置
    private TreeMap<Float, Integer> leftXMap = new TreeMap<>();
    private TreeMap<Float,Integer> rightXMap = new TreeMap<>(new Comparator<Float>() {
        @Override
        public int compare(Float o1, Float o2) {
            return Float.compare(o2,o1);
        }
    });
    private Float leftX;
    private Float rightX;


    //存放页面的文本内容
    private int MaxSize = 10;
    private LinkedList<Tu.Tuple2<Integer,List<TextBlock>>> textPagesMap = new LinkedList<>();

    //记录最后一次放入的
    private List<TextBlock> lastTextPage;

    //存放页面的第一行内容
    private LinkedList<List<Tu.Tuple2<TextPosition,RenderInfo>>> firstLineMap = new LinkedList<>();

    //存放页面的最后一行内容
    private LinkedList<List<Tu.Tuple2<TextPosition,RenderInfo>>> endLineMap = new LinkedList<>();


    private float totalLineSpace;
    private float totalLineSpaceCount;

    /**
     * 文档中有的目录层级
     */
    private boolean[] titleLevels = null;

    //字体大小映射
    private Map<Float,Integer> fontSizeMap = new HashMap<>();
    //主要字体大小
    private Float mainFontSize = 0f;


    //预热同时判断文章属于英文还是中文
    public void preHeat(PDDocument document,Integer pageNum) throws IOException {
        this.document = document;
        int numberOfPages = document.getNumberOfPages();
        int up = Math.min(numberOfPages,pageNum);
        int chineseCount = 0;
        int englishCount = 0;
        //todo 页面大小应当使用其中数量最多的
        for(int i=1;i<=up;i++){
            Tu.Tuple2<Integer, Integer> tokenNums = preHeat(i);
            chineseCount += tokenNums.getKey();
            englishCount += tokenNums.getValue();
        }
        //计算出现次数最多的文字大小
        int count = 0;
        for(Map.Entry<Float,Integer> entry:fontSizeMap.entrySet()){
            Float tmpSize = entry.getKey();
            Integer tmpNum = entry.getValue();
            if(tmpNum>count){
                mainFontSize = tmpSize;
            }
        }
        if(englishCount>chineseCount){
            language = Language.ENGLISH;
        }else{
            language = Language.CHINESE;
        }
    }

    //预热并返回中英文数量，主体字体大小
    private Tu.Tuple2<Integer,Integer> preHeat(Integer p) throws IOException {
        List<Shape> shapes = CellAnalyser.getShapes(document, p);
        List<Tu.Tuple2<Tu.Tuple2<Double, Double>, CellAnalyser.TableInfo>> tableInfos = CellAnalyser.getTableInfos(shapes);
        //tableInfo不一定是有序的，进行排序，表格从上到下
        tableInfos.sort((o1, o2) -> -Double.compare(o1.getKey().getKey(),o2.getKey().getKey()));

        float maxHeight = document.getPage(p - 1).getCropBox().getHeight();
        float maxWidth = document.getPage(p - 1).getCropBox().getWidth();
        /**
         * 文本区域
         */
        List<Tu.Tuple2<Boolean, Rectangle2D>> contentRanges = new ArrayList<>();

        //存储文本下标的位置
        List<Integer> textIndexes = new ArrayList<>();

        Double curPos = 0d; //0->841.92

        //666.5 734.46

        for(int j=0;j<tableInfos.size();j++){
            //grabText之前将除表格外的文本区域识别出来 key->以左下为坐标原点开始的数，较小 value->以左下为坐标原点结束的数，较大
            Tu.Tuple2<Double, Double> tableHeightRange = tableInfos.get(j).getKey();
            //坐标转换
            Double start = maxHeight - tableHeightRange.getValue(); //70.03
            Double end = maxHeight - tableHeightRange.getKey(); //748
            Double h = start - curPos;
            //塞入文本区域
            if(h>0){
                //记录文本区域
                int size = contentRanges.size();
                textIndexes.add(size);
                contentRanges.add(new Tu.Tuple2<>(true,new Rectangle2D.Float(0,curPos.floatValue(),maxWidth,h.floatValue())));
                curPos = end;
            }

            CellAnalyser.TableInfo tableInfo = tableInfos.get(j).getValue();
            List<CellAnalyser.Cell> cells = tableInfo.getCells();
            for(int k=0;k<cells.size();k++){
                CellAnalyser.Cell cell = cells.get(k);
                float xStart = cell.getXStart().floatValue();
                float xEnd = cell.getXEnd().floatValue();
                float width = xEnd - xStart;
                float yStart = cell.getYStart().floatValue();
                float yEnd = cell.getYEnd().floatValue();
                float height = yStart - yEnd;
                //坐标转换，原坐标是以左下角作为原点，然而pdfbox中是以左上角作为原点的
                contentRanges.add(new Tu.Tuple2<>(false,new Rectangle2D.Float(xStart,maxHeight-yStart,width,height)));
            }
        }

        //如果此时cellRanges的size为0，那么势必是页面上没有表格,新增一个文本range即可
        int size = contentRanges.size();
        if(size==0){
            textIndexes.add(size);
            contentRanges.add(new Tu.Tuple2<>(true,new Rectangle2D.Float(0,0,maxWidth,maxHeight)));
        }else{
            //如果此时的contentRanges的size不为0，那么势必页面上还有最后一个区域是文本区域
            textIndexes.add(size);
            contentRanges.add(new Tu.Tuple2<>(true,new Rectangle2D.Float(0,curPos.floatValue(),maxWidth,maxHeight-curPos.floatValue())));
        }

        List<Tu.Tuple3<List<List<Tu.Tuple2<TextPosition, RenderInfo>>>, String,Rectangle2D>> cellTexts = TextTool.grabTextEnhance(document, contentRanges, p);


        List<TextBlock> textBlocks = new ArrayList<>();

        int chineseCount = 0;
        int englishCount = 0;

        for(Integer textIndex:textIndexes){

            List<List<Tu.Tuple2<TextPosition, RenderInfo>>> range = cellTexts.get(textIndex).getValue1();
            //需要做range重排和trim
            range = UnTaggedAnalyser.sortAndTrimForRange(range);

            //从后往前倒数30个字符样本，分为中文字符和英文字符，同时统计字体大小,作为主体字体大小
            int count = 0;
            for(int i=range.size()-1;i>=0;i--){
                List<Tu.Tuple2<TextPosition, RenderInfo>> line = range.get(i);
                for(Tu.Tuple2<TextPosition, RenderInfo> tu:line){
                    String unicode = tu.getKey().getUnicode();
                    if(TextTool.isContainChinese(unicode)){
                        chineseCount ++;
                    }
                    if(TextTool.isContainEnglish(unicode)){
                        englishCount ++;
                    }
                    float fontSize = tu.getKey().getFontSize();
                    if(fontSizeMap.containsKey(fontSize)){
                        fontSizeMap.put(fontSize,fontSizeMap.get(fontSize)+1);
                    }else{
                        fontSizeMap.put(fontSize,1);
                    }
                    count++;
                    if(count==30){
                        break;
                    }
                }
            }

            //每个range取20个字符样本，分为中文字符和英文字符，
//            int count = 0;
//            for(List<Tu.Tuple2<TextPosition, RenderInfo>> line:range){
//                for(Tu.Tuple2<TextPosition, RenderInfo> tu:line){
//                    String unicode = tu.getKey().getUnicode();
//                    if(TextTool.isContainChinese(unicode)){
//                        chineseCount ++;
//                    }
//                    if(TextTool.isContainEnglish(unicode)){
//                        englishCount ++;
//                    }
//                    count++;
//                    if(count==20){
//                        break;
//                    }
//                }
//            }



            //段落判断处理
            textBlocks.add(new TextBlock(range,textIndex));


        }
        //多个块,一个块对应一个LineStatus
        this.addTextPage(textBlocks,p);



        return new Tu.Tuple2<>(chineseCount,englishCount);
    }


    public List<TextBlock> getLastTextPage(){
       return lastTextPage;
    }

//    public List<TextBlock> getSpecificTextPage(Integer pageNum){
//        return textPagesMap.getOrDefault(pageNum, null);
//    }


    public Float getAvgLineSpace(){
        if(totalLineSpaceCount==0){
            return Float.MAX_VALUE;
        }else{
            float v = totalLineSpace / totalLineSpaceCount;
            //如果不在合理范围内，比如小于20，大于1
            if(v>=20f||v<=1f){
                return Float.MAX_VALUE;
            }else{
                return v;
            }
        }
    }

    private Integer containsKey(LinkedList<Tu.Tuple2<Integer,List<TextBlock>>> list,Integer pageNum){
        for(int i=0;i<list.size();i++){
            if(list.get(i).getKey().equals(pageNum)){
                return i;
            }
        }
        return -1;
    }

    public void addTextPage(List<TextBlock> textPage,Integer pageNum){
        //如果原来就已经存在了
        Integer index = containsKey(textPagesMap, pageNum);
        if(index!=-1){
            Tu.Tuple2<Integer, List<TextBlock>> ele = textPagesMap.get(index);
            textPagesMap.remove(index);
            textPagesMap.addLast(ele);
            lastTextPage = textPage;
            return;
        }

        if(textPage.size()==0){
            return;
        }

        if(textPagesMap.size()==MaxSize){
            textPagesMap.removeFirst();
        }
        textPagesMap.addLast(new Tu.Tuple2<>(pageNum,textPage));
        TextBlock textBlock = textPage.get(0);
        List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region = textBlock.getRegion();
        if(!CollectionUtils.isEmpty(region)){
            List<Tu.Tuple2<TextPosition, RenderInfo>> line = region.get(0);
            if(firstLineMap.size()==MaxSize){
                firstLineMap.removeFirst();
            }
            firstLineMap.addLast(line);
        }

        TextBlock textBlock1 = textPage.get(textPage.size()-1);
        List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region1 = textBlock1.getRegion();
        if(!CollectionUtils.isEmpty(region1)){
            List<Tu.Tuple2<TextPosition, RenderInfo>> line = region1.get(region1.size()-1);
            if(endLineMap.size()==MaxSize){
                endLineMap.removeFirst();
            }
            endLineMap.addLast(line);
        }


        //计算lineSpace
        for(TextBlock tb:textPage){
            List<List<Tu.Tuple2<TextPosition, RenderInfo>>> rg = tb.getRegion();
            if(rg.size()<=1){
                continue;
            }
            for(int i=0;i<rg.size()-1;i++){
                List<Tu.Tuple2<TextPosition, RenderInfo>> line = rg.get(i);
                List<Tu.Tuple2<TextPosition, RenderInfo>> nextLine = rg.get(i + 1);
                if(UnTaggedAnalyser.verifyBlankLine(line)||UnTaggedAnalyser.verifyBlankLine(nextLine)){
                    //存在一个空行，跳过
                    continue;
                }
                float y = line.get(0).getKey().getY();
                float y1 = nextLine.get(0).getKey().getY();
                totalLineSpace += y1 - y;
                totalLineSpaceCount ++;
            }
        }

        //计算leftX和rightX
        textPage.stream().forEach(x->{
            List<List<Tu.Tuple2<TextPosition, RenderInfo>>> rg = x.getRegion();
            rg.stream().forEach(y->{
                if(leftXMap.containsKey(y.get(0).getKey().getX())){
                    leftXMap.put(y.get(0).getKey().getX(),leftXMap.get(y.get(0).getKey().getX())+1);
                }else{
                    leftXMap.put(y.get(0).getKey().getX(),1);
                }
                //rightX,需要加上字体宽度
                float v = y.get(y.size() - 1).getKey().getX() + y.get(y.size() - 1).getKey().getWidth();
                if(rightXMap.containsKey(v)){
                    rightXMap.put(v,rightXMap.get(v)+1);
                }else{
                    rightXMap.put(v,1);
                }
            });
        });
        for(Map.Entry<Float, Integer> entry:leftXMap.entrySet()){
            if(entry.getValue()>=3&&entry.getKey()!=Float.MAX_VALUE){
                leftX = entry.getKey();
                break;
            }
        }
        //如果此时还是为null，取第一个
        if(leftX==null){
            Optional<Map.Entry<Float, Integer>> first = leftXMap.entrySet().stream().findFirst();
            first.ifPresent(floatIntegerEntry -> leftX = floatIntegerEntry.getKey());
        }
        for(Map.Entry<Float,Integer> entry:rightXMap.entrySet()){
            if(entry.getValue()>=3&&entry.getKey()!=0){
                rightX = entry.getKey();
                break;
            }
        }
        //如果此时还是为null，取第一个
        if(rightX==null){
            Optional<Map.Entry<Float, Integer>> first = rightXMap.entrySet().stream().findFirst();
            first.ifPresent(floatIntegerEntry -> rightX = floatIntegerEntry.getKey());
        }
        lastTextPage = textPage;
    }


}
