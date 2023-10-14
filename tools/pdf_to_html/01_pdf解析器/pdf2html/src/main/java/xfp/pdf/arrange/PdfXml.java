package xfp.pdf.arrange;


import org.dom4j.Attribute;
import org.dom4j.Document;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import xfp.pdf.pojo.ContentPojo;
import xfp.pdf.pojo.ExtractPojo;
import xfp.pdf.pojo.Tu;
import xfp.pdf.tools.SettingReader;


import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;


public class PdfXml {

    private static String formContent(ContentPojo contentPojo,String indexStr){
        Integer startIndex = Integer.parseInt(indexStr.split(":")[0]);
        Integer endIndex = Integer.parseInt(indexStr.split(":")[1]);
        return formContent(contentPojo,startIndex,endIndex);
    }
    /**
     * 针对不同类型的形成不同的内容
     * @param contentPojo contentPojo
     * @param startIndex 开始下标 闭合
     * @param endIndex 结束下标 闭合
     * @return 内容
     */
    private static String formContent(ContentPojo contentPojo, Integer startIndex, Integer endIndex){
        if(startIndex<0||endIndex<0||endIndex-startIndex<0){
            return "";
        }
        List<ContentPojo.contentElement> outList = contentPojo.getOutList();
        StringBuilder sb = new StringBuilder();
        for(int i=startIndex;i<=endIndex;i++){
            ContentPojo.contentElement p = outList.get(i);
            if(p.getElementType().equals("text")||p.getElementType().equals("title")){
                sb.append("<p>");
                sb.append(p.getText().replaceAll("\n",""));
                sb.append("</p>");
                sb.append("\n");
            }else if(p.getElementType().equals("table")){
                //形成表格
                sb.append("<table border=\"1\">");
                List<ContentPojo.contentElement.InnerCell> cells = p.getCells();
                Map<Integer, List<ContentPojo.contentElement.InnerCell>> collect = cells.stream().collect(Collectors.groupingBy(ContentPojo.contentElement.InnerCell::getRow_index));
                collect.entrySet().stream().forEach(x->{
                    sb.append("<tr>").append("\n");
                    List<ContentPojo.contentElement.InnerCell> rowCells = x.getValue();
                    for(ContentPojo.contentElement.InnerCell innerCell:rowCells){
                        Integer row_span = innerCell.getRow_span();
                        Integer col_span = innerCell.getCol_span();
                        sb.append(String.format(" <td colspan=\"%s\" rowspan=\"%s\">", col_span , row_span));
                        sb.append(innerCell.getText());
                        sb.append("</td>");
                    }
                    sb.append("</tr>").append("\n");
                });
                sb.append("</table>").append("\n").append("<br/>").append("\n");
            }
        }
        return sb.toString();
    }

    /**
     * 抽取内容
     * @param doc 文档
     * @param contentPojo contentPojo
     * @param extractPojo extractPojo 对应配置文件中的抽取json
     * @return 标题和内容的结构
     */
    public static List<Tu.Tuple2<String,String>> extract(Document doc, ContentPojo contentPojo, ExtractPojo extractPojo){
        List<Tu.Tuple2<String,String>> resultList = new ArrayList<>();

        Element root = doc.getRootElement();
        List elements = root.elements();
        if(elements.size()==0){
            //策略一，可用勿删，直接按段落提取,key 第一段 第二段 第三段 value：内容
//            List<ContentPojo.Text> outList = contentPojo.getOutList();
//            int paraCount = 1;
//            for(int i=0;i<outList.size();i++){
//                String tmpStr = formContent(contentPojo, i, i);
//                if(!tmpStr.replaceAll("\n","").trim().equals("")){
//                    resultList.add(new Tu.Tuple2<>("第"+ ParaNumTool.numberToChineseCount(paraCount)+"段",formContent(contentPojo,i,i)));
//                    paraCount++;
//                }
//            }
            //策略二，解析成一整块，标题为空，方便后面以文件名作为标题
            List<ContentPojo.contentElement> outList = contentPojo.getOutList();
            resultList.add(new Tu.Tuple2<>("",formContent(contentPojo, 0, outList.size() - 1)));
            return resultList;
        }
        //如果doc不为null
        Element rootElement = doc.getRootElement();
        if(extractPojo==null){
            extractPojo = SettingReader.getPdfExtract();
        }
        Integer depth = extractPojo.getDepth();
        search(resultList,new ArrayList<>(),rootElement,0,depth+1,contentPojo);
        return resultList;
    }
    /**
     * 广度优先搜索获得所需内容
     * @param list resultList
     * @param path 当前路径
     * @param curE 当前元素
     * @param curDepth 当前深度
     * @param maxDepth 当前最大深度
     * @param contentPojo contentPojo
     */
    private static void search(List<Tu.Tuple2<String,String>> list,List<String> path,
                              Element curE,int curDepth,int maxDepth,ContentPojo contentPojo){
        curDepth++;
        if(curDepth>maxDepth){
            //不再向下遍历
            return;
        }
        String name = curE.getName();
        if(name.equals("content")){

            //先判断下级节点是否需要提取，如果不需要提取，将当前深度直接置为最大深度
            List<Element> nextElements = curE.elements();
            for(Element element:nextElements){
                //先进行一次title的判断
                boolean b = verifyIfSplitTitle(contentPojo, element);
                if(!b){
                    //如果存在任何一个下级节点不能进行拆标题，那么不再提取内容，将当前深度直接置为最大深度
                    curDepth = maxDepth;
                    break;
                }
            }

            Integer titleIndex = Integer.parseInt(curE.attribute("key").getValue());
            String title = formContent(contentPojo, titleIndex, titleIndex);
            String titlePrefix = contentPojo.getOutList().get(titleIndex).getTitlePrefix();
            String titleBody = contentPojo.getOutList().get(titleIndex).getTitleBody();

            title = title.replaceAll("\n","")
                    .replaceAll("<p>","").replaceAll("</p>","");
            String showTitle = titlePrefix+"&&" + titleBody;
            //title中可能包含内容，故从左往右遍历，找到第一个。：
            //如果title的length大于等于阈值
            String extraContent = "";


            //title中可能包含内容，故从左往右遍历，找到第一个。：
            //如果title的length大于等于阈值
            int threshold = 25;
            if(title.length()>=threshold){
                char[] charArray = title.toCharArray();
                int i;
                for(i=0;i<charArray.length;i++){
                    if(charArray[i]=='。'||charArray[i]==':'||charArray[i]=='：'){
                        break;
                    }
                }
                if(i<=charArray.length-1&&i<=threshold){
                    String tmpTitle = title;
                    title = title.substring(0,i+1);
                    if(i+1<=tmpTitle.length()-1){
                        extraContent = tmpTitle.substring(i+1,tmpTitle.length());
                    }
                }
            }
            if(!extraContent.equals("")){
                extraContent = "<p>" + extraContent + "</p>";
            }

            int threshold2 = 27;
            if(showTitle.length()>=threshold2){
                char[] charArray = showTitle.toCharArray();
                int i;
                for(i=0;i<charArray.length;i++){
                    if(charArray[i]=='。'||charArray[i]==':'||charArray[i]=='：'){
                        break;
                    }
                }
                if(i<=charArray.length-1&&i<=threshold2){
                    showTitle = showTitle.substring(0,i+1);
                }
            }


            String finalTitle;
            if(path.size()==0){
                finalTitle = showTitle;
            }else{
                finalTitle = (String.join("|", path)+"|"+showTitle);
            }
            if(curE.attribute("value")!=null&&curE.attribute("value").getValue()!=null){
                String indexStr = curE.attribute("value").getValue();
                if(curDepth != maxDepth){
                    String content = extraContent+formContent(contentPojo, indexStr);
                    if(!verifyEmptyContent(content)){
                        list.add(new Tu.Tuple2<>(finalTitle,content));
                    }
                }else{
                    //当前达到最大允许深度。
                    Integer startIndex = Integer.parseInt(indexStr.split(":")[0]);
                    Integer endIndex = findEndIndex(curE);
                    String content = extraContent+formContent(contentPojo, startIndex,endIndex);
                    if(!verifyEmptyContent(content)){
                        list.add(new Tu.Tuple2<>(finalTitle,content));
                    }
                }

            }else{
                if(extraContent.equals("")){
                    if(curDepth!=maxDepth){
                        //如果无内容，暂时不要加进去
//                        list.add(new Tu.Tuple2<>(finalTitle,"无内容"));
                    }else{
                        //当前达到最大允许深度。
                        Integer startIndex = titleIndex + 1;
                        Integer endIndex = findEndIndex(curE);
                        String content = formContent(contentPojo, startIndex,endIndex);
                        if(!verifyEmptyContent(content)){
                            list.add(new Tu.Tuple2<>(finalTitle,formContent(contentPojo, startIndex,endIndex)));
                        }
                    }
                }else{
                    if(curDepth!=maxDepth){
                        list.add(new Tu.Tuple2<>(finalTitle,extraContent));
                    }else{
                        //当前达到最大允许深度。
                        Integer startIndex = titleIndex + 1;
                        Integer endIndex = findEndIndex(curE);
                        list.add(new Tu.Tuple2<>(finalTitle,extraContent+formContent(contentPojo, startIndex,endIndex)));

                    }
                }
            }
            path.add(showTitle);

            //如果存在任何一个下级节点不能进行拆标题，那么不再提取内容
            if(curDepth!=maxDepth){
                for(Element element:nextElements){
                    search(list,new ArrayList<>(path),element,curDepth,maxDepth,contentPojo);
                }
            }

        }else if(name.equals("head")){
            String indexStr = curE.attribute("value").getValue();
            String content = formContent(contentPojo, indexStr);
            if(!verifyEmptyContent(content)){
                list.add(new Tu.Tuple2<>("头部文本",formContent(contentPojo, indexStr)));
            }
        }else if(name.equals("tail")){
            String indexStr = curE.attribute("value").getValue();
            String content = formContent(contentPojo, indexStr);
            if(!verifyEmptyContent(content)){
                list.add(new Tu.Tuple2<>("尾部文本",formContent(contentPojo, indexStr)));
            }
        } else if(name.equals("root")){
            List<Element> nextElements = curE.elements();
            for(Element element:nextElements){
                search(list,new ArrayList<>(path),element,curDepth,maxDepth,contentPojo);
            }
        }
    }
    /**
     * 判断是否是空内容
     * @param content content
     * @return 是或不是
     */
    public static Boolean verifyEmptyContent(String content){
        if(content==null){
            return true;
        }
        String s = content.replaceAll("<p>", "").replaceAll("</p>", "")
                .replaceAll("\n","");
        if(s.trim().equals("")){
            return true;
        }
        return false;
    }


    /**
     * 虽然pdf暂时没有添加隐含层，也暂时放一个该方法
     * @param level
     * @return 是或者不是
     */
    public static boolean verifyHiddenLayer(Float level){
        String s = (level + "").split("\\.")[1];
        //说明是隐藏层
        return s.equals("5");
    }
    /**
     * 判断是否是可以拆分的标题，以threshold和几个特殊符号来划分
     * @param contentPojo contentPojo
     * @param curE curE
     * @return 可以或不可以
     */
    public static boolean verifyIfSplitTitle(ContentPojo contentPojo,Element curE){
        String name = curE.getName();
        Float level = -1f;
        Attribute levelA = curE.attribute("level");
        if(levelA!=null){
            level = Float.parseFloat(levelA.getValue());
        }
        if(name.equals("content")){
            Integer titleIndex = Integer.parseInt(curE.attribute("key").getValue());
            String title = formContent(contentPojo, titleIndex, titleIndex);
            title = title.replaceAll("\n","")
                    .replaceAll("<p>","").replaceAll("</p>","");
            //title中可能包含内容，故从左往右遍历，找到第一个。：
            //如果title的length大于等于15
            String extraContent = "";

            //如果当前其实是隐含层，本身就不对标题进行拆分
            if(!verifyHiddenLayer(level)){
                int threshold = 25;
                if(title.length()>=threshold){
                    char[] charArray = title.toCharArray();
                    int i;
                    for(i=0;i<charArray.length;i++){
                        if(charArray[i]=='。'||charArray[i]==':'||charArray[i]=='：'){
                            break;
                        }
                    }
                    if(i<=charArray.length-1&&i<=threshold){
                        String tmpTitle = title;
                        title = title.substring(0,i+1);
                        if(i+1<=charArray.length-1){
                            extraContent = tmpTitle.substring(i+1,tmpTitle.length());
                        }
                    }
                }
                if(!extraContent.equals("")){
                    extraContent = "<p>" + extraContent + "</p>";
                }
            }else{
                //如果当前其实是隐含层，本身就不对标题进行拆分，故直接返回true，允许对整体内容拆分
                return true;
            }
            //判断标题的长度是否大于25，如果大于，认为标题不可拆，返回false
            if(title.length()>=25){
                return false;
            }else{
                return true;
            }
        }
        return true;
    }


    /**
     * 构建结构树，结构树可以以xml方式打印
     * @param contentPojo contentPojo
     * @return 文档结构树
     */
    public static Document buildXml(ContentPojo contentPojo) {

        List<ContentPojo.contentElement> outList = contentPojo.getOutList();

        //找到firstLevel
        Float firstLevel = Float.MAX_VALUE;

        for(ContentPojo.contentElement t:outList){
            String levelStr = t.getLevel();
            if(levelStr!=null){
                Float level = Float.parseFloat(levelStr);
                firstLevel = Math.min(firstLevel,level);
            }
        }

        if(firstLevel==Integer.MAX_VALUE){
            return null;
        }


        Document doc = DocumentHelper.createDocument();
        Element root = doc.addElement("root");
        root.addAttribute("level",0+"");

        int pos = 0;

        //存储好当前节点element
        Element curE = null;
        Float curLevel = 0f;

        boolean firstFind = false;
        while (pos != outList.size()) {
            //pos找到第一个标题
            ContentPojo.contentElement p = outList.get(pos);
            String element_type = p.getElementType();
            if (element_type.equals("text")) {
                pos++;
                continue;
            } else if (element_type.equals("title")) {
                Float level = Float.parseFloat(p.getLevel());
                //如果还没找到第一个标题
                if (!firstFind) {
                    if (firstLevel.equals(level)) {
                        //找到了第一个标题,封装head标签
                        Element freeE = root.addElement("head");
                        freeE.addAttribute("value",0 + ":" + (pos-1));

                        curE = root.addElement("content");
                        curE.addAttribute("level", level + "");
                        curE.addAttribute("key", pos + "");
                        curLevel = level;
                        firstFind = true;
                    }
                } else {
                    //找到了下一根标题,封闭上一个Ele
                    Integer titleIndex = Integer.parseInt(curE.attribute("key").getValue());
                    if (pos - titleIndex > 1) {
                        //说明有领导内容
                        curE.addAttribute("value", titleIndex + 1 + ":" + (pos - 1));
                    }
                    //判断当前level和curE
                    if (level > curLevel) {
                        //说明当前层级低，那么势必是新节点
                        curE = curE.addElement("content");
                        curE.addAttribute("level", level + "");
                        curE.addAttribute("key", pos + "");
                        curLevel = level;
                    } else {
                        //如果当前层级并不比curLevel的层级低，那么往前回溯到较高一级
                        //curLevel 3    tmpLevel 2
                        //    0 1 2 3   <- 2    找到其中的1的位置
                        while (level <= curLevel) {
                            //当tmpLevel较小
                            curE = curE.getParent();
                            curLevel = Float.parseFloat(curE.attribute("level").getValue());
                        }
                        curE = curE.addElement("content");
                        curE.addAttribute("level", level + "");
                        curE.addAttribute("key", pos + "");
                        curLevel = level;
                    }
                }
            }
            pos++;
        }


        //封闭最后一个元素
        if(curE!=null){
            //todo 可以加入横线的判断，可以加入对后面元素的行间距众数判断
            //判断是否有尾部内容,从后往前走，如果和上一个内容的距离很远，就认为是尾部文本
            int tailIndex = 0;
            Integer titleIndex = Integer.parseInt(curE.attribute("key").getValue());
            a:for(int i=outList.size()-1;i>titleIndex;i--){
                ContentPojo.contentElement cur = outList.get(i);
                ContentPojo.contentElement pre = outList.get(i - 1);
                //如果cur和pre在同一页
                if(cur.getPageNumber().equals(pre.getPageNumber())){
                    float curYEnd = cur.getYStart() + cur.getHeight();
                    float preYEnd = pre.getYStart();
                    if(preYEnd - curYEnd>60f){
                        //认为达到了不可接受的距离，如果cur不是表格或者图片的话就认为是尾部文本
                        //如果是表格或图片的话就认为实际上不存在尾部文本
                        if(cur.getElementType().equals("text")){
                            tailIndex = i;
                        }
                        //如果是表格和图片通常不认为存在尾部文本，但是如果表格中包含抄送，那么还是认为是尾部文本
                        if(cur.getElementType().equals("table")){
                            List<ContentPojo.contentElement.InnerCell> cells = cur.getCells();
                            for(ContentPojo.contentElement.InnerCell cell:cells){
                                String text = cell.getText();
                                if(text.contains("抄送")){
                                    tailIndex = i;
                                    break a;
                                }
                            }
                        }
                        break;
                    }
                }else{
                    //如果不在一页
                    float v = pre.getYStart() + pre.getPageHeight() - cur.getYStart() - cur.getHeight();
                    if(v>60f){
                        //认为达到了不可接受的距离，如果cur不是表格或者图片的话就认为是尾部文本
                        //如果是表格或图片的话就认为实际上不存在尾部文本
                        if(cur.getElementType().equals("text")){
                            tailIndex = i;
                        }
                        //如果是表格和图片通常不认为存在尾部文本，但是如果表格中包含抄送，那么还是认为是尾部文本
                        if(cur.getElementType().equals("table")){
                            List<ContentPojo.contentElement.InnerCell> cells = cur.getCells();
                            for(ContentPojo.contentElement.InnerCell cell:cells){
                                String text = cell.getText();
                                if(text.contains("送")){
                                    tailIndex = i;
                                    break a;
                                }
                            }
                        }
                        break;
                    }
                }
            }
            if(tailIndex == 0){
                if (pos - titleIndex > 1) {
                    //说明有领导内容
                    curE.addAttribute("value", titleIndex + 1 + ":" + (pos - 1));
                }
            }else{
                if(tailIndex-titleIndex>=1){
                    //说明有领导内容
                    curE.addAttribute("value", titleIndex + 1 + ":" + (tailIndex - 1));
                    Element tailE = root.addElement("tail");
                    tailE.addAttribute("value",tailIndex + ":" + (pos-1));
                }
            }
        }
        return doc;
    }

    /**
     * 递归找到当前标题下内容的最后一个元素下标
     * @param curE 当前元素
     * @return 最后一个元素下标
     */
    private static Integer findEndIndex(Element curE){
        //递归获得该节点最远影响范围
        //获得所有叶子节点
        List<Element> elements = curE.elements();
        if(elements.size()==0){
            //叶子节点
            Attribute value = curE.attribute("value");
            if(value!=null){
                return Integer.parseInt(value.getValue().split(":")[1]);
            }else{
                Attribute key = curE.attribute("key");
                return Integer.parseInt(key.getValue());
            }
        }
        int curMax = 0;
        for(Element e:elements){
            curMax = Math.max(curMax,findEndIndex(e));
        }
        return curMax;
    }

}
