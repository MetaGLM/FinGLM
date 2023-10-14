package xfp.pdf.core;

import org.apache.commons.collections4.CollectionUtils;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.text.TextPosition;
import xfp.pdf.pojo.ContentPojo;
import xfp.pdf.pojo.Language;
import xfp.pdf.pojo.LineStatus;
import xfp.pdf.pojo.Tu;
import xfp.pdf.table.CellAnalyser;
import xfp.pdf.tools.RenderInfo;


import java.awt.*;
import java.awt.geom.Rectangle2D;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;


public class BirdViewer {
    //跨多页表格合并
    // [] pre
    // [] post pre
    // []      post pre
    // []           post
    //
    // [] pre
    // [] post
    // []      pre
    // []      post
    public static void mergeTableElements(List<ContentPojo.contentElement> outList, PDDocument pdd) throws IOException{
        if(outList.size()==0){
            return;
        }
        List<Integer> indexes = new ArrayList<>();

        List<Tu.Tuple2<Integer, ContentPojo.contentElement>> continuousList = new ArrayList<>();

        for(int k=0;k<outList.size()-1;k++){
            ContentPojo.contentElement pre = outList.get(k);
            ContentPojo.contentElement post = outList.get(k + 1);

            //1.pre是表格，post是表格,上一次循环post等于pre，加入post

            //2.pre是表格，post是表格,上一次循环post不等于pre,，触发列表元素合并，加入pre和post

            //3.pre是表格，post是表格，列表为空，加入pre和post

            if(pre.getElementType().equals("table")&&post.getElementType().equals("table")){
                if(continuousList.size()==0){
                    if(ifNeedMerge(pre, post)){
                        continuousList.add(new Tu.Tuple2<>(pre.getPageNumber(),pre));
                        continuousList.add(new Tu.Tuple2<>(post.getPageNumber(),post));
                        indexes.add(k);
                        indexes.add(k+1);
                    }
                }else{
                    if(pre==continuousList.get(continuousList.size()-1).getValue()){
                        //判断post是否需要和pre合并
                        if(ifNeedMerge(pre, post)){
                            continuousList.add(new Tu.Tuple2<>(post.getPageNumber(),post));
                            indexes.add(k+1);
                        }else {
                            ContentPojo.contentElement contentElement = mergeTableElementsInner(continuousList, pdd);
                            if(contentElement !=null){
                                //删除原有下标位置
                                for(int i=indexes.size()-1;i>=0;i--){
                                    int index = indexes.get(i);
                                    outList.set(index,null);
                                }
                                outList.set(indexes.get(0), contentElement);
                            }
                            continuousList.clear();
                            indexes.clear();
                        }
                    }else{
                        ContentPojo.contentElement contentElement = mergeTableElementsInner(continuousList, pdd);
                        if(contentElement !=null){
                            //删除原有下标位置
                            for(int i=indexes.size()-1;i>=0;i--){
                                int index = indexes.get(i);
                                outList.set(index,null);
                            }
                            outList.set(indexes.get(0), contentElement);
                        }
                        continuousList.clear();
                        indexes.clear();

                        if(ifNeedMerge(pre, post)){
                            continuousList.add(new Tu.Tuple2<>(pre.getPageNumber(),pre));
                            continuousList.add(new Tu.Tuple2<>(post.getPageNumber(),post));
                            indexes.add(k);
                            indexes.add(k+1);
                        }
                    }
                }
            }
        }
        if(continuousList.size()!=0){
            ContentPojo.contentElement contentElement = mergeTableElementsInner(continuousList, pdd);
            if(contentElement !=null){
                //删除原有下标位置
                for(int i=indexes.size()-1;i>=0;i--){
                    int index = indexes.get(i);
                    outList.set(index,null);
                }
                outList.set(indexes.get(0), contentElement);
            }
            continuousList.clear();
            indexes.clear();
        }
        for(int i=outList.size()-1;i>=0;i--){
            if(outList.get(i)==null){
                outList.remove(i);
            }
        }
    }

    // [] pre
    // [] post pre
    // []      post pre
    // []           post
    private static ContentPojo.contentElement mergeTableElementsInner(List<Tu.Tuple2<Integer, ContentPojo.contentElement>> continuousList, PDDocument pdd) throws IOException {
        List<Shape> newSpecifyShapes = new ArrayList<>();
        Double preStartPoint = null;
        List<ContentPojo.contentElement.InnerCell> allCells = new ArrayList<>();
        for(int i=0;i<continuousList.size();i++){
            allCells.addAll(continuousList.get(i).getValue().getCells());
            Tu.Tuple2<Integer, ContentPojo.contentElement> tu = continuousList.get(i);
            Integer pageNum = tu.getKey();
            List<Shape> shapes = CellAnalyser.getShapes(pdd, pageNum);
            Tu.Tuple2<Tu.Tuple2<Double, Double>, CellAnalyser.TableInfo> tableInfo;
            if(i==0){
                tableInfo = CellAnalyser.getLastTableInfo(CellAnalyser.getTableInfos(shapes));
            }else {
                tableInfo = CellAnalyser.getFirstTableInfo(CellAnalyser.getTableInfos(shapes));
            }
            if(tableInfo==null){
                continue;
            }
            Double startPoint = tableInfo.getValue().getYStart();
            Double yStart = tableInfo.getKey().getKey();
            Double yEnd = tableInfo.getValue().getYEnd();
            List<Shape> specifyShapes0 = CellAnalyser.getSpecifyShapes(shapes, yStart, yEnd);

            for(Shape shape:specifyShapes0){
                double height = shape.getBounds2D().getHeight();
                double width = shape.getBounds2D().getWidth();
                double x = shape.getBounds2D().getX();
                double y = shape.getBounds2D().getY();
                double newY = y;
                if(preStartPoint!=null){
                    newY = y - yEnd + preStartPoint;
                }
                newSpecifyShapes.add(new Rectangle2D.Float((float) x, (float)newY, (float)width, (float) height));
            }
            if(preStartPoint==null){
                preStartPoint = startPoint;
            }else{
                preStartPoint = startPoint - yEnd + preStartPoint;
            }
        }
        List<Tu.Tuple2<Tu.Tuple2<Double, Double>, CellAnalyser.TableInfo>> tableInfos = CellAnalyser.getTableInfos(newSpecifyShapes);

        //tableInfos应该只有一个表格
        if(CollectionUtils.isEmpty(tableInfos)||tableInfos.size()!=1){
            return null;
        }

        //跳过preCellNum个单元格


        List<CellAnalyser.Cell> cellList = tableInfos.get(0).getValue().getCells();
        Integer colNum = tableInfos.get(0).getValue().getColNum();
        Integer rowNum = tableInfos.get(0).getValue().getRowNum();
        if(allCells.size()!=cellList.size()){
            return null;
        }

        ContentPojo.contentElement result = continuousList.get(0).getValue();


        int size = continuousList.get(0).getValue().getCells().size();
        for(int i=0;i<allCells.size();i++){
            allCells.get(i).setRow_index(cellList.get(i).getRowIndex());
            allCells.get(i).setCol_index(cellList.get(i).getColIndex());
            allCells.get(i).setCol_span(cellList.get(i).getColSpan());
            if(i>size){
                allCells.get(i).setIsNextPage(true);
            }
        }

        result.setCol_num(colNum);
        result.setRow_num(rowNum);
        result.setCells(allCells);

        return result;
    }

    private static boolean ifNeedMerge(ContentPojo.contentElement preP, ContentPojo.contentElement p){
        Integer row_num = preP.getRow_num();
        Integer tmp_row_num = p.getRow_num();
        if(row_num==null||row_num==0||tmp_row_num==null||tmp_row_num==0){
            return false;
        }

        List<ContentPojo.contentElement.InnerCell> cells = preP.getCells();
        List<ContentPojo.contentElement.InnerCell> filterCells = cells.stream().filter(x -> x.getRow_index() == 1).collect(Collectors.toList());
        if(CollectionUtils.isEmpty(filterCells)){
            return false;
        }
        Float xStart = filterCells.get(0).getXStart();
        float xEnd = filterCells.get(filterCells.size() - 1).getXStart() + filterCells.get(filterCells.size() - 1).getWidth();

        List<ContentPojo.contentElement.InnerCell> tmpCells = p.getCells();
        List<ContentPojo.contentElement.InnerCell> tmpFilterCells = tmpCells.stream().filter(x -> x.getRow_index() == 1).collect(Collectors.toList());
        if(CollectionUtils.isEmpty(tmpFilterCells)){
           return false;
        }
        Float tmpXStart = tmpFilterCells.get(0).getXStart();
        float tmpXEnd = tmpFilterCells.get(tmpFilterCells.size() - 1).getXStart() + tmpFilterCells.get(tmpFilterCells.size() - 1).getWidth();

        if(Math.abs(xStart-tmpXStart)>2||Math.abs(xEnd-tmpXEnd)>2){
            return false;
        }
        return true;
    }


    private static ContentPojo.contentElement mergePElement(ContentPojo.contentElement lastE, ContentPojo.contentElement firstE){
        List<ContentPojo.PdfStyleStruct> newStyleStruct = new ArrayList<>();
        String lastEText = lastE.getText();
        String firstEText = firstE.getText();
        String finalText = lastEText + "\n" + firstEText;
        newStyleStruct.addAll(lastE.getPdfStyleStructs());
        newStyleStruct.addAll(firstE.getPdfStyleStructs());
        lastE.setText(finalText);
        lastE.setPdfStyleStructs(newStyleStruct);
        return lastE;
    }



    public static void mergePElement(List<List<ContentPojo.contentElement>> docPages, UnTaggedContext unTaggedContext){
        if(docPages==null||docPages.size()<=1){
            return;
        }
        for(int i=0;i<docPages.size()-1;i++){
            List<ContentPojo.contentElement> curPage = docPages.get(i);
            List<ContentPojo.contentElement> nextPage = docPages.get(i + 1);
            if(CollectionUtils.isEmpty(curPage)||CollectionUtils.isEmpty(nextPage)){
                return;
            }
            ContentPojo.contentElement lastE = curPage.get(curPage.size() - 1);
            ContentPojo.contentElement firstE = nextPage.get(0);
            String lastEType = lastE.getElementType();
            String firstEType = firstE.getElementType();

            if(lastEType.equals("text")&&firstEType.equals("text")){
                LineStatus endLineStatus = lastE.getEndLineStatus();
                LineStatus startLineStatus = firstE.getStartLineStatus();
//                if(endLineStatus==LineStatus.Normal||startLineStatus==LineStatus.Normal){
                    //也许需要进行拼接，
                    //进一步查看
                    List<Tu.Tuple2<TextPosition, RenderInfo>> endLine = lastE.getEndLine();
                    List<Tu.Tuple2<TextPosition, RenderInfo>> startLine = firstE.getStartLine();
                    if(CollectionUtils.isEmpty(endLine)||CollectionUtils.isEmpty(startLine)){
                        continue;
                    }
                    //再次进行段落的判断
                    float deltaLength = Math.min(UnTaggedAnalyser.calAvgDeltaLength(endLine), UnTaggedAnalyser.calAvgDeltaLength(startLine));
                    Language language = unTaggedContext.getLanguage();
                    if(language==Language.CHINESE){
                        boolean flag3 = ParaStrategy.strategy3(endLine,startLine);
                        boolean flag7 = false;
//                    boolean flag7 = ParaStrategy.strategy7(preLine, curLine, unTaggedContext, deltaLength);
                        boolean flag8 = ParaStrategy.strategy8(endLine, startLine,unTaggedContext,deltaLength);
                        boolean flag10 = ParaStrategy.strategy10(endLine, unTaggedContext, deltaLength);
                        boolean content1 = ParaStrategy.referParaEndByContent1(endLine, unTaggedContext);

                        if(flag3||flag7||flag8||flag10||content1){
                            //不进行合并
                        }else{
                            //合并
                            ContentPojo.contentElement e = mergePElement(lastE, firstE);
                            List<ContentPojo.contentElement> list = new ArrayList<>();
                            //被合并的对象清空内容
                            firstE.setText(null);
                            list.add(firstE);
                            e.setCrossPageList(list);
                            curPage.set(curPage.size()-1,e);
                            nextPage.remove(0);
                        }

                    }else if(language==Language.ENGLISH){
                        boolean flag3 = ParaStrategy.strategy3(endLine,startLine);
                        boolean flag7 = false;
//                    boolean flag7 = ParaStrategy.strategy7(preLine, curLine, unTaggedContext, deltaLength);
                        boolean flag8 = ParaStrategy.strategy8(endLine, startLine,unTaggedContext,deltaLength);
                        boolean flag10 = ParaStrategy.strategy10(endLine, unTaggedContext, deltaLength);
                        boolean content1 = ParaStrategy.referParaEndByContent1(endLine, unTaggedContext);

                        if(flag3||flag7||flag8||flag10||content1){
                            //不进行合并
                        }else{
                            //合并
                            ContentPojo.contentElement e = mergePElement(lastE, firstE);
                            List<ContentPojo.contentElement> list = new ArrayList<>();
                            list.add(firstE);
                            e.setCrossPageList(list);
                            curPage.set(curPage.size()-1,e);
                            nextPage.remove(0);
                        }
                    }

            }
        }
    }
}
