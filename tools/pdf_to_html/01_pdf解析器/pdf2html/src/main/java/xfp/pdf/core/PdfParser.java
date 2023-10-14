package xfp.pdf.core;

import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import xfp.pdf.arrange.MarkPdf;
import xfp.pdf.pojo.BoldStatus;
import xfp.pdf.pojo.ContentPojo;
import xfp.pdf.pojo.MarkPojo;
import xfp.pdf.pojo.SearchPattern;

import java.io.IOException;
import java.util.ArrayList;
import java.util.List;


public class PdfParser {

    public static ContentPojo parsingUnTaggedPdfWithTableDetection(PDDocument pdd,boolean verifyPara) throws IOException {
        return parsingUnTaggedPdfWithTableDetectionAndPicture(pdd,null,verifyPara);
    }

    public static ContentPojo parsingUnTaggedPdfWithTableDetectionAndPicture(PDDocument pdd,String picSavePath,boolean verifyPara) throws IOException {
        int num = pdd.getNumberOfPages();
        //判断是不是ppt转成的pdf，如果这个pdf的页数大于等于2，
        //且每一页的宽度都高于高度，那么认为pdf不是word转成，直接返回空contentPojo
        boolean isDocTransPdf = false;
        if(num>=2){
            for(int i=0;i<num;i++){
                PDPage page = pdd.getPage(i);
                PDRectangle cropBox = page.getCropBox();
                float width = cropBox.getWidth();
                float height = cropBox.getHeight();
                if(width<height){
                    //有任意一页高度较高，就认为是doc转的pdf
                    isDocTransPdf = true;
                    break;
                }
            }
        }else{
            isDocTransPdf = true;
        }

        if(!isDocTransPdf){
            //返回一个空的ContentPojo即可
            ContentPojo contentPojo = new ContentPojo(new ArrayList<>());
            contentPojo.setIsPptTransPDF(true);
            return contentPojo;
        }

        UnTaggedContext untaggedContext = new UnTaggedContext();
        //预热12页的信息
        untaggedContext.preHeat(pdd,20);
        List<List<ContentPojo.contentElement>> docPages = new ArrayList<>();
        for(int i=1;i<=num;i++){
            List<ContentPojo.contentElement> page = UnTaggedAnalyser.parsePage(pdd, i, untaggedContext,picSavePath,verifyPara);
            docPages.add(page);
        }

        //合并跨页段落元素
        BirdViewer.mergePElement(docPages,untaggedContext);
        List<ContentPojo.contentElement> outList = new ArrayList<>();
        for(int i=0;i<docPages.size();i++){
            outList.addAll(docPages.get(i));
        }
        //合并跨页表格元素
        BirdViewer.mergeTableElements(outList,pdd);
        //转成json
        ContentPojo contentPojo = new ContentPojo();
        contentPojo.setOutList(outList);
        return contentPojo;
    }



    public static ContentPojo.contentElement searchOne(ContentPojo pojo, SearchPattern searchPattern){
        List<ContentPojo.contentElement> outList = pojo.getOutList();
        for(ContentPojo.contentElement c:outList){
            if(c.getText()!=null && c.getText().matches(searchPattern.getRegexStr())){
                if(searchPattern.getBoldStatus()==null){
                    return c;
                }else{
                    BoldStatus bs = MarkPdf.verifyBold(c.getPdfStyleStructs());
                    if(searchPattern.getBoldStatus() == bs){
                        return c;
                    }
                }
            }
        }
        return null;
    }

    public static List<ContentPojo.contentElement> searchList(ContentPojo pojo,List<SearchPattern> searchPatterns){
        List<ContentPojo.contentElement> resultList = new ArrayList<>();
        for(SearchPattern s:searchPatterns){
            ContentPojo.contentElement contentElement = searchOne(pojo, s);
            resultList.add(contentElement);
        }
        return resultList;
    }

    public static ContentPojo.contentElement searchTableAfterPattern(ContentPojo pojo,SearchPattern searchPattern){
        List<ContentPojo.contentElement> outList = pojo.getOutList();
        boolean flag = false;
        for(ContentPojo.contentElement c:outList){
            if(flag){
                if("table".equals(c.getElementType())){
                    return c;
                }
            }
            if(c.getText()!=null && c.getText().matches(searchPattern.getRegexStr())){
                if(searchPattern.getBoldStatus()==null){
                    flag = true;
                }else{
                    BoldStatus bs = MarkPdf.verifyBold(c.getPdfStyleStructs());
                    if(searchPattern.getBoldStatus() == bs){
                        flag = true;
                    }
                }
            }
        }
        return null;
    }

    public static List<ContentPojo.contentElement> searchListTableAfterPattern(ContentPojo pojo,List<SearchPattern> searchPatterns){
        List<ContentPojo.contentElement> resultList = new ArrayList<>();
        for(SearchPattern s:searchPatterns){
            ContentPojo.contentElement contentElement = searchTableAfterPattern(pojo, s);
            resultList.add(contentElement);
        }
        return resultList;
    }





}
