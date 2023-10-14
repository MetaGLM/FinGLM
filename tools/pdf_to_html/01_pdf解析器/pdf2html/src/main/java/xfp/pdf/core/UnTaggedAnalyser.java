package xfp.pdf.core;

import org.apache.commons.collections4.CollectionUtils;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.font.PDFontDescriptor;
import org.apache.pdfbox.pdmodel.graphics.state.RenderingMode;
import org.apache.pdfbox.text.TextPosition;

import xfp.pdf.pojo.*;
import xfp.pdf.table.CellAnalyser;
import xfp.pdf.thirdparty.GetImageEngine;
import xfp.pdf.tools.RenderInfo;
import xfp.pdf.tools.TextTool;

import java.awt.*;
import java.awt.geom.Rectangle2D;
import java.io.IOException;
import java.util.*;
import java.util.List;
import java.util.stream.Collectors;

/**
 * @ClassName UnTaggedAnalyser
 * @Description 不带标签的pdf解析工具类
 * @Author WANGHAN756
 * @Date 2021/6/21 15:32
 * @Version 1.0
 **/
public class UnTaggedAnalyser {

    static{
        System.setProperty("sun.java2d.cmm", "sun.java2d.cmm.kcms.KcmsServiceProvider");

    }
    private static GetImageEngine getImageEngine;

    public static List<ContentPojo.contentElement> parsePage(PDDocument document, Integer p, UnTaggedContext untaggedContext,String picSavePath,boolean verifyPara) throws IOException{

        List<Shape> shapes = CellAnalyser.getShapes(document, p);
        List<Tu.Tuple2<Tu.Tuple2<Double, Double>, CellAnalyser.TableInfo>> tableInfos = CellAnalyser.getTableInfos(shapes);
        //tableInfo不一定是有序的，进行排序，表格从上到下
        tableInfos.sort((o1, o2) -> -Double.compare(o1.getKey().getKey(),o2.getKey().getKey()));

        //如果是A7，是841.92
        float maxHeight = document.getPage(p - 1).getCropBox().getHeight();
        //如果是A7，是595.32
        float maxWidth = document.getPage(p - 1).getCropBox().getWidth();




        /**
         * 文本区域
         */
        List<Tu.Tuple2<Boolean, Rectangle2D>> contentRanges = new ArrayList<>();

        //存储文本下标的位置
        List<Integer> textIndexes = new ArrayList<>();

        Double curPos = 0d; //0->841.92


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
                //坐标转换，原坐标是以左下角作为原点，
                //表格range目前都为false，表示不需要获得样式
                contentRanges.add(new Tu.Tuple2<>(false,new Rectangle2D.Float(xStart,maxHeight-yStart,width,height)));
            }
        }

        //如果此时cellRanges的size为0，那么势必是页面上没有表格,新增一个文本range即可
        int size = contentRanges.size();
        if(size==0){
            textIndexes.add(size);
            //文本range目前都为true，表示需要获得样式
            contentRanges.add(new Tu.Tuple2<>(true,new Rectangle2D.Float(0,0,maxWidth,maxHeight)));
        }else{
            //如果此时的contentRanges的size不为0，那么势必页面上还有最后一个区域是文本区域，记录一下文本位置的序号
            textIndexes.add(size);
            //文本range目前都为true，表示需要获得样式
            contentRanges.add(new Tu.Tuple2<>(true,new Rectangle2D.Float(0,curPos.floatValue(),maxWidth,maxHeight-curPos.floatValue())));
        }

        List<Tu.Tuple3<List<List<Tu.Tuple2<TextPosition, RenderInfo>>>, String,Rectangle2D>> cellTexts = TextTool.grabTextEnhance(document, contentRanges, p);

        //本页最终结果Map
        Map<Integer, List<ContentPojo.contentElement>> structOutMap = new HashMap<>();

        //本页表格处理
        int pos = 0;
        for(int j=0;j<tableInfos.size();j++){
            CellAnalyser.TableInfo tableInfo = tableInfos.get(j).getValue();
            List<ContentPojo.contentElement> tableList = new ArrayList<>();
            List<CellAnalyser.Cell> cells = tableInfo.getCells();
            for(int k=0;k<cells.size();k++){
                while (textIndexes.contains(pos)){
                    //找到下一个表格位
                    pos++;
                }
                //将文本设置进去
                cells.get(k).setCell(cellTexts.get(pos).getValue2());
                pos++;
            }
            ContentPojo.contentElement t = CellAnalyser.formTable(tableInfo,p);
            t.setPageHeight(maxHeight);
            t.setPageWidth(maxWidth);
            tableList.add(t);
            structOutMap.put(pos-1,tableList);
        }

        //本页文本处理
        List<TextBlock> textBlocks = new ArrayList<>();
        for(Integer textIndex:textIndexes){
            List<List<Tu.Tuple2<TextPosition, RenderInfo>>> range = cellTexts.get(textIndex).getValue1();
            //需要做range重排和trim
            range = UnTaggedAnalyser.sortAndTrimForRange(range);
            textBlocks.add(new TextBlock(range,textIndex));
        }
        //多个块,一个块对应一个LineStatus
        untaggedContext.addTextPage(textBlocks,p);



        List<LineStatus[]> lineStatuses = new ArrayList<>();
        if(verifyPara){
            lineStatuses = UnTaggedAnalyser.parseTextBlock(untaggedContext);
        }else{
            LineStatus[] tmpLS = new LineStatus[1000];
            Arrays.fill(tmpLS, LineStatus.ParaEnd);
            for(TextBlock t:textBlocks){
                lineStatuses.add(tmpLS);
            }
        }
//        List<LineStatus[]> lineStatuses = UnTaggedAnalyser.parseTextBlock(untaggedContext);
        //结构化region
        List<List<Tu.Tuple2<TextPosition, RenderInfo>>> structRegion = new ArrayList<>();
        List<LineStatus> tmpLineStatuses = new ArrayList<>();


        int count = 0;
        for(LineStatus[] features:lineStatuses){

            TextBlock textBlock = textBlocks.get(count);
            count++;
            List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region = textBlock.getRegion();
            Integer id = textBlock.getId();

            List<ContentPojo.contentElement> contentElementList = new ArrayList<>();

            if(features==null||features.length==0){
                continue;
            }

            for(int i=0;i<features.length;i++){
                //从这里可以获得机器学习数据集
                LineStatus lineStatus = features[i];
                if(region.size()<=i){
                    break;
                }

                switch (lineStatus){
                    case ParaEnd:{
                        //断开
                        structRegion.add(region.get(i));
                        tmpLineStatuses.add(lineStatus);

                        Tu.Tuple2<String, List<ContentPojo.PdfStyleStruct>> regionString = UnTaggedAnalyser.formRegionString(structRegion);
                        Tu.Tuple4<Float, Float, Float, Float> range = UnTaggedAnalyser.formRegion(structRegion);




                        String text = regionString.getKey();

                        if(!text.replaceAll("[\\pZ]","").trim().equals("")){
                            ContentPojo.contentElement t = new ContentPojo.contentElement();
                            t.setText(text);
                            t.setPdfStyleStructs(regionString.getValue());
                            t.setElementType("text");
                            t.setPageNumber(p);
                            t.setPageHeight(maxHeight);
                            t.setPageWidth(maxWidth);
                            if(range!=null){
                                Float xStart = range.getValue1();
                                Float xEnd = range.getValue2();
                                Float yStart = maxHeight -  range.getValue3();
                                Float yEnd = maxHeight - range.getValue4();

                                t.setXStart(xStart);
                                t.setYStart(yStart);
                                t.setWidth(xEnd-xStart);
                                t.setHeight(yEnd-yStart);
                            }

                            if(structRegion.size()>=1){
                                t.setStartLine(structRegion.get(0));
                                t.setStartLineStatus(tmpLineStatuses.get(0));
                                t.setEndLine(structRegion.get(structRegion.size()-1));
                                t.setEndLineStatus(tmpLineStatuses.get(tmpLineStatuses.size()-1));
                            }
                            contentElementList.add(t);
                        }
                        structRegion.clear();
                        tmpLineStatuses.clear();
                    }break;
                    case Normal:{
                        //继续
                        structRegion.add(region.get(i));
                        tmpLineStatuses.add(lineStatus);
                    }break;
                    case Header:{
                        //跳过
                    }
                    case Footer:{
                        //跳过
                    }break;
                }
            }
            //如果最后位置没有paraEnd，这里加进去
            if(structRegion.size()!=0){
                Tu.Tuple2<String, List<ContentPojo.PdfStyleStruct>> regionString = UnTaggedAnalyser.formRegionString(structRegion);
                Tu.Tuple4<Float, Float, Float, Float> range = UnTaggedAnalyser.formRegion(structRegion);

                String text = regionString.getKey();
                if(!text.replaceAll("[\\pZ]","").trim().equals("")){
                    ContentPojo.contentElement t = new ContentPojo.contentElement();
                    t.setText(regionString.getKey());
                    t.setPdfStyleStructs(regionString.getValue());
                    t.setElementType("text");
                    t.setPageNumber(p);
                    t.setPageHeight(maxHeight);
                    t.setPageWidth(maxWidth);
                    if(range!=null){
                        Float xStart = range.getValue1();
                        Float xEnd = range.getValue2();
                        Float yStart = maxHeight -  range.getValue3();
                        Float yEnd = maxHeight - range.getValue4();

                        t.setXStart(xStart);
                        t.setYStart(yStart);
                        t.setWidth(xEnd-xStart);
                        t.setHeight(yEnd-yStart);
                    }

                    if(structRegion.size()>=1){
                        t.setStartLine(structRegion.get(0));
                        t.setStartLineStatus(tmpLineStatuses.get(0));
                        t.setEndLine(structRegion.get(structRegion.size()-1));
                        t.setEndLineStatus(tmpLineStatuses.get(tmpLineStatuses.size()-1));
                    }
                    contentElementList.add(t);
                }

                structRegion.clear();
                tmpLineStatuses.clear();
            }

            structOutMap.put(id, contentElementList);
        }


        //对structOutMap排序然后拍平
        List<ContentPojo.contentElement> pageContentList = new ArrayList<>();
        structOutMap.entrySet().stream().sorted(Comparator.comparingInt(Map.Entry::getKey)).forEach(x->{
            pageContentList.addAll(x.getValue());
        });

        /**
         * 图片区域
         */
        if(picSavePath==null){
            return pageContentList;
        }
        if(getImageEngine==null){
            getImageEngine = new GetImageEngine(picSavePath);
        }else{
            getImageEngine.clearList();
        }
        PDPage pdPage = document.getPages().get(p-1);
        getImageEngine.processPage(pdPage);
        List<Tu.Tuple2<Integer, Rectangle2D.Float>> pics = getImageEngine.getPics();
        //将图片插入到list中去
        int i = 0;
        if(pics.size()!=0){
            for(Tu.Tuple2<Integer,Rectangle2D.Float> pic:pics){
                double yStart =  pic.getValue().getY();
                while (true){
                    if(i==pageContentList.size()){
                        ContentPojo.contentElement contentElement = new ContentPojo.contentElement();
                        contentElement.setElementType("pic");
                        contentElement.setText(picSavePath + "/" + pic.getKey()+".png");
                        contentElement.setPageNumber(p);
                        pageContentList.add(contentElement);
                        break;
                    }
                    if(pageContentList.get(i).getYStart() > yStart){
                        i++;
                    }else{
                        ContentPojo.contentElement contentElement = new ContentPojo.contentElement();
                        contentElement.setElementType("pic");
                        contentElement.setText(picSavePath + "/" + pic.getKey()+".png");
                        contentElement.setPageNumber(p);
                        if(i==0){
                            pageContentList.add(0,contentElement);
                            i++;
                        }else{
                            pageContentList.add(i-1,contentElement);
                        }

                        break;
                    }
                }

            }
        }

        return pageContentList;
    }



    public static List<LineStatus[]> parseTextBlock(UnTaggedContext untaggedContext){
        List<TextBlock> blockList = untaggedContext.getLastTextPage();
        List<LineStatus[]> resultList = new ArrayList<>();
        int count = 0;
        for(TextBlock textBlock:blockList){
            count++;
            List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region = textBlock.getRegion();
            //深拷贝一份region，不要对原来的region产生影响，TODO 后续用下标控制会更好
            List<List<Tu.Tuple2<TextPosition, RenderInfo>>> newRegion = new ArrayList<>(region);
            if(CollectionUtils.isEmpty(newRegion)){
                resultList.add(null);
                continue;
            }
            LineStatus[] lineStatuses = new LineStatus[newRegion.size()];
            Arrays.fill(lineStatuses, LineStatus.Normal);

            Integer offset = 0;
            //如果是第一个，判断是否是页眉
            if(count==1){
                int i = verifyHeader(untaggedContext,newRegion.get(0));
                if(i==1){
                    lineStatuses[0] = LineStatus.Header;
                    newRegion.remove(0);
                    offset = 1;
                }
            }


            //如果是最后一个了，判断是否是页码
            if(count == blockList.size() && !newRegion.isEmpty()){
                boolean b = verifyPagination(untaggedContext,newRegion.get(newRegion.size() - 1));
                if(b){
                    lineStatuses[lineStatuses.length-1] = LineStatus.Footer;
                    newRegion.remove(newRegion.size() - 1);
                }
            }
            if(CollectionUtils.isEmpty(newRegion)){
                resultList.add(lineStatuses);
            }else{
                resultList.add(parseTextBlock(newRegion, lineStatuses, untaggedContext,offset));
            }


//            System.out.println("此时lineStatuses size："+lineStatuses.length);
//            System.out.println("此时region size"+region.size());
        }
        return resultList;
    }

   
    private static LineStatus[] parseTextBlock(List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region,LineStatus[] lineStatuses,UnTaggedContext unTaggedContext
                                                ,Integer offset){
        if(region.size()<=2){
            //此时文本块的size只有2，但是大于0
            if(region.size()==1){
                //如果只有1，那么自成一段
                lineStatuses[0] = LineStatus.ParaEnd;
            }else{
                //如果是2，那么第二行肯定是一个段结尾，就是要判断一下第一行是否是段结尾
                //使用preInfo
                float rightX = unTaggedContext.getRightX();
                float x = region.get(0).get(region.get(0).size() - 1).getKey().getX()+region.get(0).get(region.get(0).size() - 1).getKey().getWidth();
                float deltaLength = calAvgDeltaLength(region.get(0));
                if(comparePos(x,rightX,deltaLength)){
                    //有缩进，是段结尾
                    lineStatuses[0+offset] = LineStatus.ParaEnd;
                }else{
                    lineStatuses[0+offset] = LineStatus.Normal;
                }
                lineStatuses[1+offset] = LineStatus.ParaEnd;
            }
        }else{
            for(int i=0;i<region.size()-2;i++){
                List<Tu.Tuple2<TextPosition, RenderInfo>> curLine = region.get(i + 1);

                if(curLine.size()==0){
                    continue;
                }
//                logger.info("current process line:{}",curLine);

                List<Tu.Tuple2<TextPosition, RenderInfo>> preLine = region.get(i);
                List<Tu.Tuple2<TextPosition, RenderInfo>> postLine = region.get(i + 2);

                float deltaLength = 0f;

                if(unTaggedContext.getLanguage()== Language.CHINESE){
                    deltaLength = calAvgDeltaLength(curLine);
                }else if(unTaggedContext.getLanguage()==Language.ENGLISH){
                    deltaLength = calAvgDeltaLength(curLine)*4;
                }



                Language language = unTaggedContext.getLanguage();
                if(language==Language.CHINESE){
//                    boolean flag1 = ParaStrategy.strategy1(preLine, curLine, deltaLength);
//                    boolean flag2 = ParaStrategy.strategy2(curLine, postLine, deltaLength);
//                    boolean flag3 = ParaStrategy.strategy3(curLine, postLine);
//                    boolean flag4 = ParaStrategy.strategy4(curLine, postLine);
//                    boolean flag5 = ParaStrategy.strategy5(preLine, curLine, postLine, unTaggedContext, deltaLength);
//                    boolean flag6 = ParaStrategy.strategy6(curLine, unTaggedContext, deltaLength);
//                    boolean content1 = ParaStrategy.referParaEndByContent1(curLine, unTaggedContext);
//
//                    if(flag1||flag2||flag3||flag4||flag5||flag6){
//                        lineStatuses[i+1+offset] = LineStatus.ParaEnd;
//                    }else{
//                        if(content1){
//                            lineStatuses[i+1+offset] = LineStatus.ParaEnd;
//                        }
//                    }
                    boolean flag3 = ParaStrategy.strategy3(curLine,postLine);
                    boolean flag7 = false;
//                    boolean flag7 = ParaStrategy.strategy7(preLine, curLine, unTaggedContext, deltaLength);
                    boolean flag8 = ParaStrategy.strategy8(curLine, postLine,unTaggedContext,deltaLength);
                    boolean flag9 = ParaStrategy.strategy9(preLine, curLine, postLine);
                    boolean flag10 = ParaStrategy.strategy10(curLine, unTaggedContext, deltaLength);
                    boolean flag11 = ParaStrategy.strategy11(preLine,curLine, postLine, unTaggedContext, deltaLength);
                    boolean content1 = ParaStrategy.referParaEndByContent1(curLine, unTaggedContext);

                    if(flag3||flag7||flag8||flag9||flag10||flag11||content1){
                        lineStatuses[i+1+offset] = LineStatus.ParaEnd;
                    }
//                    logger.info("current process line flag:{},{},{},{},{},{}",flag3,flag7,flag8,flag9,flag10,content1);


//                    logger.info("current process line flag:{},{},{},{},{},{},{}",flag1,flag2,flag3,flag4,flag5,flag6,content1);
                }else if(language==Language.ENGLISH){
                    boolean flag3 = ParaStrategy.strategy3(curLine,postLine);
                    boolean flag7 = false;
//                    boolean flag7 = ParaStrategy.strategy7(preLine, curLine, unTaggedContext, deltaLength);
                    boolean flag8 = ParaStrategy.strategy8(curLine, postLine,unTaggedContext,deltaLength);
                    boolean flag9 = ParaStrategy.strategy9(preLine, curLine, postLine);
                    boolean flag10 = ParaStrategy.strategy10(curLine, unTaggedContext, deltaLength);
                    boolean content1 = ParaStrategy.referParaEndByContent1(curLine, unTaggedContext);

                    if(flag3||flag7||flag8||flag9||flag10||content1){
                        lineStatuses[i+1+offset] = LineStatus.ParaEnd;
                    }
//                    logger.info("current process line flag:{},{},{},{},{},{}",flag3,flag7,flag8,flag9,flag10,content1);
                }


            }
            //势必会漏掉开头和结尾两部分，单独进行处理
            //对于开头来说，需要满足一些策略 它的下一行有缩进,或者本行末尾有缩进即可
            List<Tu.Tuple2<TextPosition, RenderInfo>> first = region.get(0);
            float deltaLength = 0f;

            if(unTaggedContext.getLanguage()==Language.CHINESE){
                deltaLength = calAvgDeltaLength(first);
            }else if(unTaggedContext.getLanguage()==Language.ENGLISH){
                deltaLength = calAvgDeltaLength(first)*4;
            }
            if(region.size()==1){
                lineStatuses[0+offset] = LineStatus.ParaEnd;
            }else{
                List<Tu.Tuple2<TextPosition, RenderInfo>> second = region.get(0);
                boolean flag3 = ParaStrategy.strategy3(first,second);
                boolean flag8 = ParaStrategy.strategy8(first, second,unTaggedContext,deltaLength);
                boolean flag10 = ParaStrategy.strategy10(first, unTaggedContext, deltaLength);
                boolean content1 = ParaStrategy.referParaEndByContent1(first, unTaggedContext);
                if(flag3||flag8||flag10||content1){
                    lineStatuses[0+offset] = LineStatus.ParaEnd;
                }
            }


            //对于结尾来说,它的末尾有明显缩进即可
            List<Tu.Tuple2<TextPosition, RenderInfo>> last = region.get(region.size() - 1);
            if(unTaggedContext.getLanguage()==Language.CHINESE){
                deltaLength = calAvgDeltaLength(first);
            }else if(unTaggedContext.getLanguage()==Language.ENGLISH){
                deltaLength = calAvgDeltaLength(first)*4;
            }
            if(ParaStrategy.lastLineStrategy1(last,unTaggedContext,deltaLength)||ParaStrategy.referParaEndByContent1(last, unTaggedContext)){
                lineStatuses[region.size()-1+offset] = LineStatus.ParaEnd;
            }
        }
        return lineStatuses;
    }


    public static Map<Integer, Tu.Tuple2<String,List<ContentPojo.PdfStyleStruct>>> formBlockString(List<TextBlock> textBlocks){
        Map<Integer, Tu.Tuple2<String,List<ContentPojo.PdfStyleStruct>>> map = new HashMap<>();
        for(TextBlock tb:textBlocks){
            Integer id = tb.getId();
            List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region = tb.getRegion();
            Tu.Tuple2<String, List<ContentPojo.PdfStyleStruct>> strAndStyle = formRegionString(region);
            map.put(id,strAndStyle);
        }
        return map;
    }

    public static Tu.Tuple2<String,List<ContentPojo.PdfStyleStruct>> formRegionString(List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region){
        List<ContentPojo.PdfStyleStruct> styleList = new ArrayList<>();
        StringBuilder sb = new StringBuilder();
        for(List<Tu.Tuple2<TextPosition, RenderInfo>> line:region){
            formLineString(line,styleList,sb);
        }
        //删除最后一个\n
        if(sb.length()!=0&&sb.charAt(sb.length()-1)=='\n'){
            sb.delete(sb.length()-1,sb.length());
            styleList.remove(styleList.size()-1);
        }
        return new Tu.Tuple2<>(sb.toString(),styleList);
    }

    private static Tu.Tuple4<Float,Float,Float,Float> formRegion(List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region){
        if(CollectionUtils.isEmpty(region)){
            return null;
        }

        float minLeftX = Float.MAX_VALUE;
        float maxRightX = 0f;
        float upBound = 0f;
        float bottomBound = 0f;

        for(int i=0;i<region.size();i++){
            List<Tu.Tuple2<TextPosition, RenderInfo>> line = region.get(i);
            if(!CollectionUtils.isEmpty(line)){
                float leftX = line.get(0).getKey().getX();
                minLeftX = Math.min(minLeftX,leftX);
                float rightX = line.get(line.size() - 1).getKey().getX() + line.get(line.size() - 1).getKey().getWidth();
                maxRightX = Math.max(maxRightX,rightX);
            }else{
                continue;
            }
            //注意，坐标轴此时在左上角
            if(i==0){
                Tu.Tuple2<TextPosition, RenderInfo> tu = line.get(0);
                //默认都是某一行文字的下方,所以要减去字体高度
                upBound = tu.getKey().getY() - tu.getKey().getHeight();
            }
            if(i==region.size()-1){
                Tu.Tuple2<TextPosition, RenderInfo> tu = line.get(0);
                bottomBound = tu.getKey().getY();
            }
        }
        if(minLeftX==Float.MAX_VALUE||maxRightX==0f||upBound==0f||bottomBound==0f){
            return null;
        }else{
//            String format = String.format("%s,%s,%s,%s", minLeftX, maxRightX, bottomBound, upBound);
//            System.out.println(format);
            return new Tu.Tuple4<>(minLeftX,maxRightX,bottomBound,upBound);
        }

    }


    /**
     * 固化了一个比较基础的title判断
     * @param line
     * @return
     */
    public static boolean isTitle(List<Tu.Tuple2<TextPosition, RenderInfo>> line){
        String str = UnTaggedAnalyser.formLineString(line);
        if(str.matches("[一二三四五六七八九十]{1,3}[、.．][\\s\\S]*")){
            return true;
        }
        if(str.matches("[(（][一二三四五六七八九十]{1,3}[)）][、.．]?[\\s\\S]*")){
            return true;
        }
        if(str.matches("[1-9]{1,3}[.,、，．][\\s\\S]*")){
            return true;
        }
        if(str.matches("[1-9]{1,3}[.][1-9]{1,3}[\\s\\S]*")){
            return true;
        }
        if(str.matches("[(（]?[1-9]{1,2}[)）][、.．]?[\\s\\S]*")){
            return true;
        }
        if(str.matches("[①②③④⑤⑥⑦⑧⑨⑩][\\s\\S]*")){
            return true;
        }
        return false;
    }

    public static void main(String[] args) {
        String str = "6．RUN服务体系汇报";
        boolean matches = str.matches("[1-9]{1,2}[.,、，．][\\s\\S]*");
        System.out.println(matches);
    }


    public static String formLineString(List<Tu.Tuple2<TextPosition, RenderInfo>> line){
        if(CollectionUtils.isEmpty(line)){
            return "";
        }
        StringBuilder sb = new StringBuilder();
        for(Tu.Tuple2<TextPosition, RenderInfo> tu:line){
            TextPosition tp = tu.getKey();
            sb.append(tp.getUnicode());
        }
        return sb.toString();
    }

    public static void formLineString(List<Tu.Tuple2<TextPosition, RenderInfo>> line,List<ContentPojo.PdfStyleStruct> styleList,StringBuilder sb){
        for(Tu.Tuple2<TextPosition, RenderInfo> tu:line){
            ContentPojo.PdfStyleStruct pdfStyleStruct = new ContentPojo.PdfStyleStruct();
            TextPosition tp = tu.getKey();
            //如果是空字符串，这里的ri有可能为null
            RenderInfo ri = tu.getValue();


            pdfStyleStruct.setText(tp.getUnicode());
            sb.append(tp.getUnicode());
            if(ri!=null){
                pdfStyleStruct.setLineWidth(ri.getLineWidth());
                pdfStyleStruct.setRenderingMode(ri.getRenderingMode().toString());
            }

            pdfStyleStruct.setRotation(tp.getRotation());
            pdfStyleStruct.setX(tp.getX());
            pdfStyleStruct.setY(tp.getY());
            pdfStyleStruct.setWidth(tp.getWidth());
            pdfStyleStruct.setHeight(tp.getHeight());

            pdfStyleStruct.setFontSize(tp.getFontSize());
            pdfStyleStruct.setFontSizePt(tp.getFontSizeInPt());
            //如果是空字符串，这里的getFont的结果可能为null
            if(tp.getFont()!=null){
                PDFontDescriptor fontDescriptor = tp.getFont().getFontDescriptor();
                if(fontDescriptor!=null){
                    pdfStyleStruct.setFontName(fontDescriptor.getFontName());
                }
                if(fontDescriptor!=null){
                    pdfStyleStruct.setFontWeight(fontDescriptor.getFontWeight());
                }
                if(fontDescriptor!=null){
                    pdfStyleStruct.setCharSet(fontDescriptor.getCharSet());
                }
            }
            styleList.add(pdfStyleStruct);
        }
        sb.append("\n");
        styleList.add(null);
    }


    public static List<List<Tu.Tuple2<TextPosition, RenderInfo>>> sortAndTrimForRange(List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region){
        return trimRange(sortForRange(region));
    }

    public static List<List<Tu.Tuple2<TextPosition, RenderInfo>>> sortForRange(List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region){
        return region.stream().sorted((o1, o2) -> {
            Tu.Tuple2<TextPosition, RenderInfo> p1 = o1.get(0);
            Tu.Tuple2<TextPosition, RenderInfo> p2 = o2.get(0);
            TextPosition t1 = p1.getKey();
            TextPosition t2 = p2.getKey();
            float y1 = t1.getY();
            float y2 = t2.getY();
            return Float.compare(y1, y2);
        }).collect(Collectors.toList());
    }

    public static List<List<Tu.Tuple2<TextPosition, RenderInfo>>> trimRange(List<List<Tu.Tuple2<TextPosition, RenderInfo>>> region){
        if(CollectionUtils.isEmpty(region)) {
            return region;
        }
        int pre = 0;
        int pos = region.size()-1;
        //向右找到第一个不为空行的行
        while (true){
            if(pre==region.size()){
                break;
            }
            if(verifyBlankLine(region.get(pre))){
                pre++;
            }else{
                break;
            }
        }
        if(pre==region.size()){
           //说明全部都是空行
            return new ArrayList<>();
        }else{
            //向左找到第一个不为空的行
            while (true){
                if(pos==-1){
                    break;
                }
                if(verifyBlankLine(region.get(pos))){
                    pos--;
                }else{
                    break;
                }
            }
            //此时绝对能够找到，故再遍历两次，删除从0到pre的行，删除从pos到region.size()-1的行
            int count = region.size()-1;

            for(int i=0;i<pre;i++){
                region.remove(0);
            }

            for(int i=count;i>pos;i--){
                region.remove(region.size()-1);
            }
            return region;
        }

    }

    public static List<Tu.Tuple2<TextPosition, RenderInfo>> trimLine(List<Tu.Tuple2<TextPosition, RenderInfo>> line){
        if(CollectionUtils.isEmpty(line)) {
            return line;
        }
        int pre = 0;
        int pos = line.size()-1;
        //向右找到第一个不为空行的行
        while (true){
            if(pre==line.size()){
                break;
            }
            if(verifyBlankToken(line.get(pre).getKey())){
                pre++;
            }else{
                break;
            }
        }
        if(pre==line.size()){
            //说明全部都是空行
            return new ArrayList<>();
        }else{
            //向左找到第一个不为空的行
            while (true){
                if(pos==-1){
                    break;
                }
                if(verifyBlankToken(line.get(pos).getKey())){
                    pos--;
                }else{
                    break;
                }
            }
            //此时绝对能够找到，故再遍历两次，删除从0到pre的行，删除从pos到region.size()-1的行
            int count = line.size()-1;

            for(int i=0;i<pre;i++){
                line.remove(0);
            }

            for(int i=count;i>pos;i--){
                line.remove(line.size()-1);
            }
            return line;
        }
    }


    public static boolean verifyBlankLine(List<Tu.Tuple2<TextPosition, RenderInfo>> line){
        //判断某一行是否是空行，方便做类似trim的操作，但是此时的单位是行
        StringBuilder sb = new StringBuilder();
        for(Tu.Tuple2<TextPosition, RenderInfo> tu:line){
            String unicode = tu.getKey().getUnicode();
            sb.append(unicode.replaceAll("[\\pZ]","").trim());
        }
        return sb.toString().equals("");
    }

    private static boolean verifyBlankToken(TextPosition t){
        String unicode = t.getUnicode();
        String token = unicode.replaceAll("[\\pZ]", "").trim();
        return token.equals("");
    }


    private static int verifyHeader(UnTaggedContext unTaggedContext,List<Tu.Tuple2<TextPosition, RenderInfo>> line){
        LinkedList<List<Tu.Tuple2<TextPosition, RenderInfo>>> firstLineMap = unTaggedContext.getFirstLineMap();
        int size = firstLineMap.size();
        int count = 0;
        String curLine = formLineString(line);
        for(List<Tu.Tuple2<TextPosition, RenderInfo>> l:firstLineMap){
            String s = formLineString(l);
            if(curLine.equals(s)){
                count++;
            }
        }
        //数量至少为2，且大于总页面数的一半
        if(count>=2 && count>=size/2){
            return 1;
        }

        /*
         如果第一行的字体大小和第二行不相同，或者第一行和第二行的字体大小与第三行不相同（第一行和第二行相同的情况下），显著要小一点
         容易误判
         */
//        if(lastTextPage.size()==0){
//            return 0;
//        }
//        Float avgLineSpace = untaggedContext.getAvgLineSpace();
//        if(region.size()<=1){
//            return 0;
//        }else{
//            //只比较第一行和第二行
//            List<Tu.Tuple2<TextPosition, RenderInfo>> firstLine = region.get(0);
//            List<Tu.Tuple2<TextPosition, RenderInfo>> secondLine = region.get(1);
//            if(verifyBlankLine(firstLine)||verifyBlankLine(secondLine)){
//                return 0;
//            }else{
//                float y = firstLine.get(0).getKey().getY();
//                float fontSize = firstLine.get(0).getKey().getFontSize();
//
//                float y1 = secondLine.get(0).getKey().getY();
//                float fontSize1 = secondLine.get(0).getKey().getFontSize();
//
//                if(y1-y>=1.5*avgLineSpace&&fontSize!=fontSize1){
//                    return 1;
//                }
//            }
//
//        }

        return 0;
    }


    //判断出页码，首先这个文本块需要位于页面的下方，其长度较短，且包含数字
    private static boolean verifyPagination(UnTaggedContext unTaggedContext,List<Tu.Tuple2<TextPosition, RenderInfo>> line){
        String str = formLineString(line);
        if(str.length()<=7&&!str.endsWith("。")&&!str.endsWith(".")){
            //结尾不是。.
            for(Tu.Tuple2<TextPosition, RenderInfo> tu:line){
                String unicode = tu.getKey().getUnicode();
                if(unicode==null||unicode.length()==0){
                    return false;
                }
                if(Character.isDigit(unicode.charAt(0))){
                    return true;
                }
            }
        }

        //再判断相似度
        LinkedList<List<Tu.Tuple2<TextPosition, RenderInfo>>> endLineMap = unTaggedContext.getEndLineMap();

        //至少和3页相似度在百分之50以上,有可能包括自己这一页
        int count = 0;
        String targetStr = formLineString(line);
        for(List<Tu.Tuple2<TextPosition, RenderInfo>> curLine:endLineMap){
            String tmpStr = formLineString(curLine);
            double p = 1 - calStrDistance(tmpStr,targetStr)*1.0/Math.max(targetStr.length(),tmpStr.length());
            if(p>0.5){
                count++;
            }
            if(count==2){
                return true;
            }
        }
        return false;
    }

    private static int calStrDistance(String str1, String str2) {
        char[] a = str1.toCharArray();
        char[] b = str2.toCharArray();
        int[][] len = new int[a.length + 1][b.length + 1];
        for (int i = 0; i < len.length; i++) {
            len[i][0] = i;
        }
        for (int j = 0; j < len[0].length; j++) {
            len[0][j] = j;
        }
        for (int i = 1; i < len.length; i++) {
            for (int j = 1; j < len[0].length; j++) {
                if (a[i - 1] == b[j - 1]) {
                    len[i][j] = len[i - 1][j - 1];
                } else {
                    len[i][j] = Math.min(Math.min(len[i - 1][j], len[i - 1][j - 1]), len[i][j - 1]) + 1;
                }
            }
        }
        return len[len.length - 1][len[0].length - 1];
    }


    public static float calAvgDeltaLength(List<Tu.Tuple2<TextPosition, RenderInfo>> line){
        float aggr = 0f;
        int sizeMinus = 0;
        for(Tu.Tuple2<TextPosition, RenderInfo> p:line){
            TextPosition tp = p.getKey();
            if(isPresetTextPosition(tp)){
                sizeMinus ++;
                continue;
            }
            float width = tp.getWidth();
            aggr += width;
        }
        int i = line.size() - sizeMinus;
        if(i!=0){
            return aggr/i;
        }else{
            return Float.MAX_VALUE;
        }
    }

    private static boolean isPresetTextPosition(TextPosition tp){
        if(tp.getPageWidth()==-1||tp.getPageWidth()==-2){
            return true;
        }else{
            return false;
        }
    }


    public static boolean comparePos(Float pre,Float post,float tolerance){
        if(post-pre>tolerance){
            return true;
        }else{
            return false;
        }
    }

    public static boolean compareTokenRender(RenderInfo pre,RenderInfo post){
        RenderingMode preRenderingMode = pre.getRenderingMode();
        RenderingMode postRenderingMode = post.getRenderingMode();
        if(preRenderingMode!=postRenderingMode){
            return true;
        }else {
            return false;
        }
    }


    public static boolean compareTokenFont(List<Tu.Tuple2<TextPosition, RenderInfo>> line1,List<Tu.Tuple2<TextPosition, RenderInfo>> line2){
        //获得行内最常见字体+渲染方式+Font weight
        Map<String, Integer> fontMap = new HashMap<>();
        //找到两行最常用的两种字体
        Tu.Tuple2<String, String> preMostCommonFonts = findMostCommonFont(line1, fontMap);
        Tu.Tuple2<String, String> postMostCommonFont = findMostCommonFont(line2, fontMap);

        String preFirst = preMostCommonFonts.getKey();
        String preSecond = preMostCommonFonts.getValue();

        String postFirst = postMostCommonFont.getKey();
        String postSecond = postMostCommonFont.getValue();

        if(!preFirst.equals("")&&(preFirst.equals(postFirst)||preFirst.equals(postSecond))){
            return false;
        }
        if(!preSecond.equals("")&&(preSecond.equals(postFirst)||preSecond.equals(postSecond))){
            return false;
        }
        return true;
    }

    public static Tu.Tuple2<String,String> findMostCommonFont(List<Tu.Tuple2<TextPosition, RenderInfo>> line, Map<String,Integer> fontMap){
        fontMap.clear();
        //获得行内最常见字体+渲染方式+Font weight
        for(Tu.Tuple2<TextPosition, RenderInfo> tu:line){
            if(tu.getKey().getFont()==null||tu.getKey().getFont().getFontDescriptor()==null){
                continue;
            }
            String fontName = tu.getKey().getFont().getFontDescriptor().getFontName();
            float fontWeight = tu.getKey().getFont().getFontDescriptor().getFontWeight();
            RenderingMode renderingMode = tu.getValue().getRenderingMode();
            String key = fontName+renderingMode+fontWeight;
            if(fontMap.containsKey(key)){
                fontMap.put(key,fontMap.get(key)+1);
            }else{
                fontMap.put(key,1);
            }
        }

        List<Map.Entry<String, Integer>> collect = fontMap.entrySet().stream().sorted(new Comparator<Map.Entry<String, Integer>>() {
            @Override
            public int compare(Map.Entry<String, Integer> o1, Map.Entry<String, Integer> o2) {
                return (o2.getValue() - o1.getValue());
            }
        }).collect(Collectors.toList());

        String first = "";
        String second = "";

        if(!CollectionUtils.isEmpty(collect)){
            if(collect.size()==1){
                first = collect.get(0).getKey();
            }else{
                first = collect.get(0).getKey();
                //第二种字体至少要达到3个元素以上,避免一些特殊字符会有相同的格式
                Integer count = collect.get(1).getValue();
                if(count>3){
                    second = collect.get(1).getKey();
                }
            }
        }
        return new Tu.Tuple2<>(first,second);

    }

    public static boolean compareFirstTokenPos(TextPosition pre,TextPosition post,float tolerance){
        float preX = pre.getX();
        float postX = post.getX();
        if(postX-preX>tolerance){
            return true;
        }else{
            return false;
        }
    }

    public static boolean compareEndTokenPos(TextPosition pre,TextPosition post,float tolerance){
        float preX = pre.getX();
        float postX = post.getX();
        if(preX-postX>tolerance){
            return true;
        }else{
            return false;
        }
    }

    public static Tu.Tuple2<Float,Float> findMostCommonFontSize(List<Tu.Tuple2<TextPosition, RenderInfo>> line,Map<Float, Integer> map){
        map.clear();
        line.forEach(x->{
            float fontSize = x.getKey().getFontSize();
            if(map.containsKey(fontSize)){
                map.put(fontSize,map.get(fontSize)+1);
            }else{
                map.put(fontSize,1);
            }
        });

        List<Map.Entry<Float, Integer>> collect = map.entrySet().stream().sorted(new Comparator<Map.Entry<Float, Integer>>() {
            @Override
            public int compare(Map.Entry<Float, Integer> o1, Map.Entry<Float, Integer> o2) {
                return -Integer.compare(o1.getValue(), o2.getValue());
            }
        }).collect(Collectors.toList());
        //注意，如果相同则返回两个一样的
        if(collect.size()==1){
            Float first = collect.get(0).getKey();
            return new Tu.Tuple2<>(first,first);
        }else if(collect.size()>=2){
            Float first = collect.get(0).getKey();
            Float second = collect.get(1).getKey();
            return new Tu.Tuple2<>(first,second);
        }
        return null;
    }

    public static Tu.Tuple2<String,String> findMostCommonRenderingMode(List<Tu.Tuple2<TextPosition, RenderInfo>> line,Map<String, Integer> map){
        map.clear();
        line.forEach(x->{
            if(x.getValue()!=null&&x.getValue().getRenderingMode()!=null){
                String renderingMode = x.getValue().getRenderingMode().toString();
                if(map.containsKey(renderingMode)){
                    map.put(renderingMode,map.get(renderingMode)+1);
                }else{
                    map.put(renderingMode,1);
                }
            }
        });

        List<Map.Entry<String, Integer>> collect = map.entrySet().stream().sorted(new Comparator<Map.Entry<String, Integer>>() {
            @Override
            public int compare(Map.Entry<String, Integer> o1, Map.Entry<String, Integer> o2) {
                return -Integer.compare(o1.getValue(), o2.getValue());
            }
        }).collect(Collectors.toList());
        //注意，如果相同则返回两个一样的
        if(collect.size()==1){
            String first = collect.get(0).getKey();
            return new Tu.Tuple2<>(first,first);
        }else if(collect.size()>=2){
            String first = collect.get(0).getKey();
            String second = collect.get(1).getKey();
            return new Tu.Tuple2<>(first,second);
        }
        return null;
    }





}
