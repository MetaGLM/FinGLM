package xfp.pdf.arrange;

import org.apache.commons.collections4.CollectionUtils;
import xfp.pdf.pojo.BoldStatus;
import xfp.pdf.pojo.ContentPojo;
import xfp.pdf.pojo.MarkPojo;
import xfp.pdf.tools.SettingReader;
import xfp.pdf.tools.TextTool;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;


public class MarkPdf {


    public static void markTitleSep(ContentPojo contentPojo){
        MarkPojo markPojo = SettingReader.getPdfMark();
        List<MarkPojo.TitlePattern> titlePatterns = markPojo.getTitlePatterns();
        List<ContentPojo.contentElement> outList = contentPojo.getOutList();
        List<Integer> boldStatuses = new ArrayList<>();
        boldStatuses.add(2);
        for(int i=0;i<outList.size();i++){
            ContentPojo.contentElement p = outList.get(i);
            if(p.getElementType().equals("table")||p.getElementType().equals("pic")){
                continue;
            }
            List<ContentPojo.PdfStyleStruct> styles = p.getPdfStyleStructs();

            if(styles!=null){
                for(int j=0;j<titlePatterns.size();j++){
                    MarkPojo.TitlePattern titlePattern = titlePatterns.get(j);
                    String bold = titlePattern.getBold();
                    String pattern = titlePattern.getPattern();
                    int boldStatus = 0;
                    if(bold!=null){
                        boldStatus = verifyBold(styles).getStatus();
                        if(boldStatuses.contains(boldStatus)){
                            p.setElementType("title");
                            continue;
                        }
                    }
                        //先看整体是否是符合要求的
                        if(p.getText().matches(pattern)){
                            p.setElementType("title");
                        }

                }
            }
        }
    }

    /**
     * 根据配置文件对标题进行标记
     * @param contentPojo contentPojo
     * @param markPojo markPojo 对应配置文件中的标记json
     */
    public static void markTitle(ContentPojo contentPojo, MarkPojo markPojo){
        if(markPojo==null){
            markPojo = SettingReader.getPdfMark();
        }
        List<MarkPojo.TitlePattern> titlePatterns = markPojo.getTitlePatterns();
        //按order进行排序
        List<MarkPojo.TitlePattern> sortedTitlePatterns = titlePatterns.stream().filter(x->x.getOrder()!=null).sorted(new Comparator<MarkPojo.TitlePattern>() {
            @Override
            public int compare(MarkPojo.TitlePattern o1, MarkPojo.TitlePattern o2) {
                return o1.getOrder() - o2.getOrder();
            }
        }).collect(Collectors.toList());

        List<ContentPojo.contentElement> outList = contentPojo.getOutList();

        for(int i=0;i<outList.size();i++){
            ContentPojo.contentElement p = outList.get(i);
            if(p.getElementType().equals("table")||p.getElementType().equals("pic")){
                continue;
            }
            List<ContentPojo.PdfStyleStruct> styles = p.getPdfStyleStructs();

            if(styles!=null){
                for(int j=0;j<sortedTitlePatterns.size();j++){
                    MarkPojo.TitlePattern titlePattern = sortedTitlePatterns.get(j);
                    String bold = titlePattern.getBold();
                    List<Integer> boldStatuses = new ArrayList<>();
                    String pattern = titlePattern.getPattern();
                    String firstPattern = titlePattern.getFirstPattern();
                    Float level = titlePattern.getLevel();
                    boldStatuses.add(1);boldStatuses.add(2);boldStatuses.add(0);
                    int boldStatus = 0;
                    if(bold!=null){
                        boldStatuses = Arrays.stream(bold.split(",")).map(Integer::parseInt).collect(Collectors.toList());
                        boldStatus = verifyBold(styles).getStatus();
                    }
                    if(boldStatuses.contains(boldStatus)){
                        //先看整体是否是符合要求的
                        if(p.getText().matches(pattern)){
                            p.setElementType("title");
                            p.setLevel(level+"");
                            //捕获组抽取标题部分
                            Pattern pa = Pattern.compile(pattern);
                            Matcher m = pa.matcher(p.getText());
                            if(m.find()){
                                if(m.groupCount()==2){
                                    p.setTitlePrefix(m.group(1));
                                    p.setTitleBody(m.group(2));

                                }
                            }

                            if(firstPattern!=null){
                                if(p.getText().matches(firstPattern)){
                                    //如果是本级标题的初始标题
                                    p.setTitleStart(true);
                                }else{
                                    p.setTitleStart(false);
                                }
                            }
                        }
                    }
                }
            }
        }
        //过滤掉目录部分，找到一级标题的最初的位置，如果有多个，就定位到第最后一个的位置，那么前面如果有任何标题就设置为文本
        Optional<MarkPojo.TitlePattern> first = titlePatterns.stream().filter(x -> x.getLevel() == 1f).findFirst();
        if(first.isPresent()){
            List<Integer> firstHeaderList = new ArrayList<>();
            for(int i=0;i<outList.size();i++){
                ContentPojo.contentElement p = outList.get(i);
                String element_type = p.getElementType();
                if(element_type.equals("title")){
                    String level = p.getLevel();
                    Boolean titleStart = p.getTitleStart();
                    if(titleStart!=null&&titleStart&&level.equals("1.0")){
                        //第一级别标题
                        firstHeaderList.add(i);
                    }
                }
            }
            if(!CollectionUtils.isEmpty(firstHeaderList)){
                Integer firstHeaderIndex = firstHeaderList.get(firstHeaderList.size() - 1);
                for(int i=0;i<firstHeaderIndex;i++){
                    ContentPojo.contentElement p = outList.get(i);
                    if(p.getElementType().equals("title")){
                        p.setElementType("text");
                        p.setLevel(null);
                        p.setTitleStart(null);
                    }
                }
            }
        }
    }
    /**
     *  多种情况是加粗的
     *  1.fontName:带SimHei，如ABCDEE+SimHei
     *  2.fontWeight大于400
     *  3.renderingMode为FILL_STROKE
     *  注意只考虑中英文文本的加粗情况,特殊符号跳过
     *  0->不包含，1->包含部分，2->全部加粗
     */
    public static BoldStatus verifyBold(List<ContentPojo.PdfStyleStruct> styles){
        int countAll = 0;
        int countBold = 0;
        for(int i=0;i<styles.size();i++){
            ContentPojo.PdfStyleStruct style = styles.get(i);
            if(style!=null){
                String text = style.getText();
                if(TextTool.isContainEnglish(text)||TextTool.isContainChinese(text)){
                    countAll++;
                    String fontName = style.getFontName();
                    Float fontWeight = style.getFontWeight();
                    String renderingMode = style.getRenderingMode();
                    if((fontName!=null&&fontName.contains("SimHei"))||(fontWeight!=null&&fontWeight>400)||
                            (renderingMode!=null&&renderingMode.equals("FILL_STROKE"))){
                        countBold++;
                    }
                }
            }
        }
        if(countAll!=0){
            if(countBold==countAll){
                return BoldStatus.FullBord;
            }else if(countBold>=1){
                return BoldStatus.PartBord;
            }else{
                return BoldStatus.NoBord;
            }
        }else{
            return BoldStatus.NoBord;
        }
    }

}
