package xfp.pdf.table;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.ToString;
import org.apache.commons.collections4.CollectionUtils;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.common.PDRectangle;



import xfp.pdf.pojo.ContentPojo;
import xfp.pdf.pojo.Tu;
import xfp.pdf.thirdparty.CustomPDFRenderer;
import  xfp.pdf.thirdparty.CustomPageDrawer;
import xfp.pdf.tools.TextTool;


import java.awt.*;
import java.awt.geom.Rectangle2D;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.util.List;
import java.util.*;
import java.util.stream.Collectors;


public class CellAnalyser {
    @Data
    @ToString
    @NoArgsConstructor
    @AllArgsConstructor
    public static class TableInfo{
        private Integer rowNum;
        private Integer colNum;
        private Double xStart;
        private Double yStart;
        private Double xEnd;
        private Double yEnd;
        private List<Cell> cells;
    }
    @Data
    @ToString
    @NoArgsConstructor
    public static class Cell implements Comparable<Cell>{
        private Double xStart;
        private Double xEnd;
        private Double yStart;
        private Double yEnd;
        private Integer colSpan;
        private Integer rowSpan;
        private Integer rowIndex;
        private Integer colIndex;
        private String cell;
        // 1 rowSpan开始，0 延续，-1 rowSpan结束
        private Integer rowSpanStatus;
        public Cell(Double xStart, Double xEnd, Double yStart, Double yEnd) {
            this.xStart = xStart;
            this.xEnd = xEnd;
            this.yStart = yStart;
            this.yEnd = yEnd;
        }
        @Override
        public int compareTo(Cell o) {
            //行少的在前面，行多的在后面
            Integer rowIndex1 = this.getRowIndex();
            Integer colIndex1 = this.getColIndex();
            Integer rowIndex2 = o.getRowIndex();
            Integer colIndex2 = o.getColIndex();
            if(rowIndex1<rowIndex2){
                return -1;
            }else if(rowIndex1>rowIndex2){
                return 1;
            }else {
                if(colIndex1<colIndex2){
                    return -1;
                }else if(colIndex1>colIndex2){
                    return 1;
                }else {
                    return 0;
                }
            }
        }
    }

    /**
     * 横线最短的限度
     */
    private static final double minHorizonLineLength = 60d;
    /**
     * 竖线最短的限度
     */
    private static final double minVerticalLineLength = 15d;

    /**
     * 竖线最大允许宽度 TODO 这里是否使用线的y范围比x的范围更大来判断是否是竖线更好？
     */
    private static final double maxVerticalLineWidth = 3d;

    /**
     * 横线最大允许宽度
     */
    private static final double maxHorizonLineWidth = 3d;


//    public static List<Rectangle> getRectangles(PDDocument doc,int pageNum) throws IOException {
//        CustomPDFRenderer renderer = new CustomPDFRenderer(doc);
//        BufferedImage image = renderer.renderImage(pageNum-1);
//        CustomPageDrawer drawer = renderer.getDrawer();
//
//        List<Rectangle> fillRec = drawer.getFillRec();
//        List<Rectangle> strokeRec = drawer.getStrokeRec();
//
//        if(strokeRec.size()!=0){
//            return strokeRec;
//        }else{
//            return fillRec;
//        }
//    }

    public static List<Shape> getShapes(PDDocument doc,int pageNum) throws IOException {
        CustomPDFRenderer renderer = new CustomPDFRenderer(doc);
        BufferedImage image = renderer.renderImage(pageNum-1);
        CustomPageDrawer drawer = renderer.getDrawer();

        List<Shape> tableLines = drawer.getTableLines();
        List<Shape> fillLines = drawer.getFillLines();
        List<Shape> strokeLines = drawer.getStrokeLines();
//        List<Shape> fillAndStrokeLine = drawer.getFillAndStrokeLine();
//
//        return fillAndStrokeLine;

        if(strokeLines.size()!=0){
            return strokeLines;
        }else{
            return fillLines;
        }
//        return tableLines;
    }

    //使用heightStart和heightEnd做一层过滤
    public static List<Shape> getSpecifyShapes(List<Shape> shapes, Double heightStart, Double heightEnd){
        return shapes.stream().filter(x -> {
            double yStart = x.getBounds2D().getY() + 5d;
            double yEnd = x.getBounds2D().getY() + x.getBounds2D().getHeight() - 5d;
            return yStart >= heightStart && yEnd <= heightEnd;
        }).collect(Collectors.toList());
    }


    public static Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo> getLastTableInfo(List<Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo>> resultList){
        Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo> curLast = null;
        Double curStart = Double.MAX_VALUE;
        for(Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo> tu:resultList){
            Double tmpStart = tu.getKey().getKey();
            if(tmpStart<curStart){
                curLast = tu;
                curStart = tmpStart;
            }
        }
        return curLast;
    }

    //找到页面的第一个表格
    public static Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo> getFirstTableInfo(List<Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo>> resultList){
        Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo> curFirst = null;
        Double curStart = 0d;
        for(Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo> tu:resultList){
            Double tmpStart = tu.getKey().getKey();
            if(tmpStart>curStart){
                curFirst = tu;
                curStart = tmpStart;
            }
        }
        return curFirst;
    }


    public static TableInfo getSpecifyTableInfo(List<Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo>> resultList, Double heightStart, Double heightEnd){
        List<Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo>> list = resultList.stream().filter(x -> {
            Tu.Tuple2<Double, Double> key = x.getKey();
            Double yStart = key.getKey();
            Double yEnd = key.getValue();
            return yStart <= heightStart && yEnd >= heightEnd;
        }).collect(Collectors.toList());
        if(list.size()!=0){
            return list.get(0).getValue();
        }else{
            return new TableInfo(0,0,0d,0d,0d,0d,new ArrayList<>());
        }
    }

//    public static List<Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo>> getTableInfosRec(List<Rectangle> rectangles){
//
//    }

    public static List<Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo>> getTableInfos(List<Shape> tableLines) {
        /**tableLines并不一定是线，可能是一块区域，当w和h同时大于6时，我们认为这是一块区域，该区域可以生成4条线 */
        List<TableLine.VerticalLine> verticalLines = new ArrayList<>();
        List<TableLine.HorizonLine> horizonLines = new ArrayList<>();
        for(Shape shape:tableLines){
            Rectangle2D bounds2D = shape.getBounds();
            double width = bounds2D.getWidth();
            double height = bounds2D.getHeight();
            if(bounds2D.getWidth()*bounds2D.getHeight()>=300000){
                continue;
            }
            if(width>=8&&height>=8){
                continue;
            }

            if(width<maxVerticalLineWidth){
                verticalLines.add(new TableLine.VerticalLine(bounds2D.getX(), bounds2D.getY(),
                        bounds2D.getY() + bounds2D.getHeight()));
            }
            if(height<maxHorizonLineWidth){
                horizonLines.add(new TableLine.HorizonLine(bounds2D.getY(), bounds2D.getX(),
                        bounds2D.getX() + bounds2D.getWidth()));
            }


//            if(width>=6&&height>=6){
//                //bottom line  x y w h
//                TableLine.HorizonLine bottomLine = new TableLine.HorizonLine(bounds2D.getY(), bounds2D.getX(), bounds2D.getX() + bounds2D.getWidth());
////                TableLine.HorizonLine bottomLine = new TableLine.HorizonLine(shape.getBounds2D().getY(), shape.getBounds2D().getX(), 585);
//                //top line
//                TableLine.HorizonLine topLine = new TableLine.HorizonLine(bounds2D.getY()+bounds2D.getHeight(), bounds2D.getX(), bounds2D.getX() + bounds2D.getWidth());
////                TableLine.HorizonLine topLine = new TableLine.HorizonLine(shape.getBounds2D().getY()+shape.getBounds2D().getHeight(), shape.getBounds2D().getX(), 585);
//                //left line
//                TableLine.VerticalLine leftLine = new TableLine.VerticalLine(bounds2D.getX(),bounds2D.getY(),bounds2D.getY()+bounds2D.getHeight());
//                //right line
//                TableLine.VerticalLine rightLine = new TableLine.VerticalLine(bounds2D.getX()+bounds2D.getWidth(),bounds2D.getY(),bounds2D.getY()+bounds2D.getHeight());
//                horizonLines.add(bottomLine);
//                horizonLines.add(topLine);
//                verticalLines.add(leftLine);
//                verticalLines.add(rightLine);
//            }else{
//                if(width<maxVerticalLineWidth){
//                    verticalLines.add(new TableLine.VerticalLine(bounds2D.getX(), bounds2D.getY(),
//                            bounds2D.getY() + bounds2D.getHeight()));
//                }
//                if(height<maxHorizonLineWidth){
//                    horizonLines.add(new TableLine.HorizonLine(bounds2D.getY(), bounds2D.getX(),
//                            bounds2D.getX() + bounds2D.getWidth()));
//                }
//            }
        }


        /**---------------------分离出并合并相连的竖线------------------------------------------ */
        //统一x值
        unifyVerticalLine(verticalLines);
        Collections.sort(verticalLines);
        //将相连的竖线连接在一起
        double curX = 0;
        TableLine.VerticalLine vL = null;
        List<TableLine.VerticalLine> newVerticalLines = new ArrayList<>();
        for(TableLine.VerticalLine v:verticalLines){
            double x = v.getX();
            if(curX==0){
                curX = x;
            }
            if(curX==x){
                if(vL==null){
                    vL = v;
                }else{
                    double yEnd = vL.getYEnd();
                    double yStart = v.getYStart();
                    if(yStart-yEnd<2.0f){
                        //可以接到一块
                        vL = TableLine.connectVLine(vL, v);
                    }else{
                        //断开
                        if(vL.length>=minVerticalLineLength) {
                            newVerticalLines.add(vL);
                        }
                        vL = v;
                    }
                }
            }else{
                //断开
                if(vL!=null){
                    if(vL.length>=minVerticalLineLength) {
                        newVerticalLines.add(vL);
                    }
                    vL = v;
                }
                curX = x;
            }
        }
        if(vL!=null){
            if(vL.length>=minVerticalLineLength) {
                newVerticalLines.add(vL);
            }
        }

        /**---------------------分离出并合并相连的横线------------------------------------------ */
//        List<TableLine.HorizonLine> horizonLines = tableLines.stream().filter(x -> {
//            double height = x.getBounds2D().getHeight();
//            return height < maxHorizonLineWidth;
//        }).map(x -> new TableLine.HorizonLine(x.getBounds2D().getY(), x.getBounds2D().getX(),
//                x.getBounds2D().getX() + x.getBounds2D().getWidth()))
//                .collect(Collectors.toList());
        //统一y值
        unifyHorizonLine(horizonLines);
        Collections.sort(horizonLines);
        //横线连接
        double curY = 0;
        TableLine.HorizonLine hl = null;
        List<TableLine.HorizonLine> newHorizonLines = new ArrayList<>();
        for(TableLine.HorizonLine h:horizonLines){
            double y = h.getY();
            if(curY==0){
                curY = y;
            }
            if(curY==y){
                if(hl==null){
                    hl = h;
                }else{
                    double xEnd = hl.getXEnd();
                    double xStart = h.getXStart();
                    if(xStart-xEnd<2.0f){
                        //可以接到一块
                        hl = TableLine.connectHLine(hl, h);
                    }else{
                        //断开
                        if(hl.length>=minHorizonLineLength){
                            newHorizonLines.add(hl);
                        }
                        hl = h;
                    }
                }
            }else{
                //断开
                if(hl!=null){
                    if(hl.length>=minHorizonLineLength){
                        newHorizonLines.add(hl);
                    }
                    hl = h;
                }
                curY = y;
            }
        }
        if(hl!=null){
            if(hl.length>=minHorizonLineLength){
                newHorizonLines.add(hl);
            }
        }

        if(newHorizonLines.size()!=0){
            TableLine.HorizonLine firstLine = newHorizonLines.get(0);
            double y = firstLine.getY();
            if(newVerticalLines.size()>=2){
                TableLine.VerticalLine left = newVerticalLines.get(0);
                double leftYEnd = left.getYEnd();
                double leftX = left.getX();
                TableLine.VerticalLine right = newVerticalLines.get(newVerticalLines.size() - 1);
                double rightYEnd = right.getYEnd();
                double rightX = right.getX();
                if(leftYEnd-y>10d&&rightYEnd-y>10d){
                    newHorizonLines.add(0,new TableLine.HorizonLine(leftYEnd,leftX,rightX));
                }
            }
        }


        stretchVerticalLine(newVerticalLines);
        stretchHorizonLine(newHorizonLines);
        /**---------------------表格区域判断----------------------------------------------- */

        List<Tu.Tuple2<Double,Double>> rangeList = new ArrayList<>();
        for (TableLine.VerticalLine verticalLine : newVerticalLines) {
            double yStart = verticalLine.getYStart();
            double yEnd = verticalLine.getYEnd();
            rangeList.add(new Tu.Tuple2<>(yStart, yEnd));
        }
        for(int i=0;i<rangeList.size()-1;i++){
            Tu.Tuple2<Double,Double> tuple = rangeList.get(i);
            Double yStart = tuple.getKey();
            Double yEnd = tuple.getValue();
            for(int j=i+1;j<rangeList.size();j++){
                Tu.Tuple2<Double,Double> curTuple = rangeList.get(j);
                Double tmpYStart = curTuple.getKey();
                Double tmpYEnd = curTuple.getValue();
                if(yStart<=tmpYStart&&yEnd>=tmpYEnd){
                    //tuple完全包括curTuple，tuple的值有意义
                    curTuple.setKey(yStart);
                    curTuple.setValue(yEnd);
                    tuple.setKey(-1d);
                    tuple.setValue(-1d);
                }else if(tmpYStart<=yStart&&tmpYEnd>=yEnd){
                    //curTuple完全包括tuple，curTuple的值有意义
                    tuple.setKey(-1d);
                    tuple.setValue(-1d);
                }else if(modifyEqual(tmpYStart,yStart)&&modifyEqual(tmpYEnd,yEnd)){
                    //存在modifyEqual的情况，取范围最大的
                    curTuple.setKey(Math.min(tmpYStart,yStart));
                    curTuple.setValue(Math.max(tmpYEnd,yEnd));
                    tuple.setKey(-1d);
                    tuple.setValue(-1d);
                }
            }
        }
        List<Tu.Tuple2<Double,Double>> ranges = rangeList.stream().filter(x -> x.getKey() != -1d).collect(Collectors.toList());

        List<Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo>> result = ranges.stream().map(x -> {
            Double yStart = x.getKey()-5d;
            Double yEnd = x.getValue()+5d;
            List<TableLine.HorizonLine> horizonLines1 = newHorizonLines.stream().filter(y -> {
                double y1 = y.getY();
                return yStart <= y1 && yEnd >= y1;
            }).collect(Collectors.toList());

            List<TableLine.VerticalLine> verticalLines1 = newVerticalLines.stream().filter(y -> {
                double yStart1 = y.getYStart();
                double yEnd1 = y.getYEnd();
                return yStart <= yStart1 && yEnd >= yEnd1;
            }).collect(Collectors.toList());

            /**
             * ---------------
             *   |   |    |
             * --------------
             * 表格可能缺乏左右边框，补上左右边框，取横线的最小值和最大值
             */
            if(horizonLines1.size()!=0){
                TableLine.HorizonLine lastHLine = horizonLines1.get(horizonLines1.size()-1);
                double xs = lastHLine.getXStart();
                double xe = lastHLine.getXEnd();
                double lhy = lastHLine.getY();
                TableLine.HorizonLine firstHLine = horizonLines1.get(0);
                double fhy = firstHLine.getY();
                if(verticalLines1.size()!=0){
                    TableLine.VerticalLine firstVLine = verticalLines1.get(0);
                    TableLine.VerticalLine lastVLine = verticalLines1.get(verticalLines1.size() - 1);
                    double fxv = firstVLine.getX();
                    double lxv = lastVLine.getX();
                    if(fxv-xs>20.0f){
                        verticalLines1.add(0,new TableLine.VerticalLine(xs,lhy,fhy));
                    }
                    if(xe-lxv>20.0f){
                        verticalLines1.add(new TableLine.VerticalLine(xe,lhy,fhy));
                    }
                }
            }

            TableInfo tableInfo = getTableInfo(horizonLines1, verticalLines1);

            return new Tu.Tuple2<Tu.Tuple2<Double, Double>, TableInfo>(x, tableInfo);
        }).collect(Collectors.toList());
        return result;
    }

    public static ContentPojo.contentElement formTable(TableInfo tableInfo, Integer pageNum, PDDocument pdd) throws IOException {
        PDRectangle cropBox = pdd.getPage(pageNum-1).getCropBox();
        //如果是A7页面，高度是841.92f
        float maxHeight = cropBox.getHeight();

        List<Rectangle2D> cellRanges = new ArrayList<>();
        List<ContentPojo.contentElement.InnerCell> innerCells = tableInfo.getCells().stream().map(x -> {
            Integer rowIndex = x.getRowIndex();
            Integer colIndex = x.getColIndex();
            Integer rowSpan = x.getRowSpan();
            Integer colSpan = x.getColSpan();
            float xStart = x.getXStart().floatValue();
            float xEnd = x.getXEnd().floatValue();
            float width = xEnd - xStart;
            float yStart = x.getYStart().floatValue();
            float yEnd = x.getYEnd().floatValue();
            float height = yStart - yEnd;

            cellRanges.add(new Rectangle2D.Double(xStart, maxHeight - yStart, width, height));
            ContentPojo.contentElement.InnerCell innerCell = new ContentPojo.contentElement.InnerCell();
            innerCell.setRow_index(rowIndex);
            innerCell.setCol_index(colIndex);
            innerCell.setRow_span(rowSpan);
            innerCell.setCol_span(colSpan);


            return innerCell;
        }).collect(Collectors.toList());

        List<Tu.Tuple2<String, Rectangle2D>> cellTexts = TextTool.grabText(pdd, cellRanges, pageNum);

        for(int i=0;i<innerCells.size();i++){
            Tu.Tuple2<String, Rectangle2D> tmp = cellTexts.get(i);
            innerCells.get(i).setText(tmp.getKey());
            innerCells.get(i).setXStart((float) tmp.getValue().getX());
            innerCells.get(i).setYStart((float) tmp.getValue().getY());
            innerCells.get(i).setHeight((float) tmp.getValue().getHeight());
            innerCells.get(i).setWidth((float) tmp.getValue().getWidth());
        }


        Integer rowNum = tableInfo.getRowNum();
        Integer colNum = tableInfo.getColNum();
        ContentPojo.contentElement table = new ContentPojo.contentElement(pageNum, "table", rowNum, colNum, innerCells);
        return table;
    }

    public static ContentPojo.contentElement formTable(TableInfo tableInfo, Integer pageNum) {
        Integer rowNum = tableInfo.getRowNum();
        Integer colNum = tableInfo.getColNum();
        List<ContentPojo.contentElement.InnerCell> innerCells = tableInfo.getCells().stream().map(x -> {
            Integer rowIndex = x.getRowIndex();
            Integer colIndex = x.getColIndex();
            Integer rowSpan = x.getRowSpan();
            Integer colSpan = x.getColSpan();
            float xStart = x.getXStart().floatValue();
            float xEnd = x.getXEnd().floatValue();
            float width = xEnd - xStart;
            float yStart = x.getYStart().floatValue();
            float yEnd = x.getYEnd().floatValue();
            float height = yStart - yEnd;

            String cell = x.getCell();

            ContentPojo.contentElement.InnerCell innerCell = new ContentPojo.contentElement.InnerCell();
            innerCell.setRow_index(rowIndex);
            innerCell.setCol_index(colIndex);
            innerCell.setRow_span(rowSpan);
            innerCell.setCol_span(colSpan);

            innerCell.setXStart(xStart);
            innerCell.setYStart(yStart);
            innerCell.setWidth(width);
            innerCell.setHeight(height);

            innerCell.setText(cell);
            return innerCell;
        }).collect(Collectors.toList());
        ContentPojo.contentElement table = new ContentPojo.contentElement(pageNum, "table", rowNum, colNum, innerCells);
        Double xStart = tableInfo.getXStart();
        Double xEnd = tableInfo.getXEnd();
        Double yStart = tableInfo.getYStart();
        Double yEnd = tableInfo.getYEnd();

        table.setXStart(xStart.floatValue());
        table.setYStart(yStart.floatValue());
        double height = yEnd - yStart;
        table.setHeight((float) height);
        double width = xEnd - xStart;
        table.setWidth((float) width);


        return table;
    }

    public static boolean modifyEqual(Double a,Double b){
        return Math.abs(b - a) <= 3d;
    }

    private static TableInfo getTableInfo(List<TableLine.HorizonLine> horizonLines,
                                          List<TableLine.VerticalLine> verticalLines){
        List<TableLine.HorizonLine> needRemoveLine = new ArrayList<>();
        for(TableLine.HorizonLine horizonLine:horizonLines){
            double xStart = horizonLine.getXStart();
            double xEnd = horizonLine.getXEnd();
            double y = horizonLine.getY();
            int crossCount = 0;
            for(TableLine.VerticalLine verticalLine:verticalLines){
                if(crossCount==2){
                    break;
                }
                double verticalLineX = verticalLine.getX();
                double verticalLineYStart = verticalLine.getYStart();
                double verticalLineYEnd = verticalLine.getYEnd();
                if(xStart<verticalLineX&&xEnd>verticalLineX){
                    if(verticalLineYStart<y&&verticalLineYEnd>y){
                        crossCount ++;
                    }
                }
            }
            if(crossCount<2){
                needRemoveLine.add(horizonLine);
            }
        }
        horizonLines.removeAll(needRemoveLine);

        //horizonLines中有可能有需要

        List<Cell> list = new ArrayList<>();
        int rowNum = 0;
        int colNum = 0;
        int curRowIndex = 0;

        Double tableXStart = 0d;
        Double tableXEnd = 0d;
        Double tableYStart = 0d;
        Double tableYEnd = 0d;

        //为什么horizonLine是一个列表呢，是因为可能出现合并单元格导致horizonLine断开的情况，这样就变成了y值相同的多个horizonLine
        Map<Double, List<TableLine.HorizonLine>> collect = horizonLines.stream().collect(Collectors.groupingBy(TableLine.HorizonLine::getY));
        List<Map.Entry<Double, List<TableLine.HorizonLine>>> horizonList = collect.entrySet().stream().sorted(new Comparator<Map.Entry<Double, List<TableLine.HorizonLine>>>() {
            @Override
            public int compare(Map.Entry<Double, List<TableLine.HorizonLine>> o1, Map.Entry<Double, List<TableLine.HorizonLine>> o2) {
                return Double.compare(o2.getKey(),o1.getKey());
            }
        }).collect(Collectors.toList());

        if(!CollectionUtils.isEmpty(horizonList)){
            //第一条横线和最后一条横线，人为使其扩展至页面最大值
            Map.Entry<Double, List<TableLine.HorizonLine>> fistLineListMap = horizonList.get(0);
            List<TableLine.HorizonLine> firstLineList = fistLineListMap.getValue();
            if(!CollectionUtils.isEmpty(firstLineList)){
                TableLine.HorizonLine horizonLine = firstLineList.get(0);
                horizonLine.setXStart(-Integer.MAX_VALUE);
                //todo，后续最好根据页面最大范围来设置
                horizonLine.setXEnd(Integer.MAX_VALUE);
                //抹掉其他横线
                List<TableLine.HorizonLine> newFirstHorizonLine = new ArrayList<>();
                newFirstHorizonLine.add(horizonLine);
                fistLineListMap.setValue(newFirstHorizonLine);
            }
            Map.Entry<Double, List<TableLine.HorizonLine>> lastLineListMap = horizonList.get(horizonList.size()-1);
            List<TableLine.HorizonLine> lastLineList = lastLineListMap.getValue();
            if(!CollectionUtils.isEmpty(lastLineList)){
                TableLine.HorizonLine horizonLine = lastLineList.get(0);
                horizonLine.setXStart(-Integer.MAX_VALUE);
                //todo，后续最好根据页面最大范围来设置
                horizonLine.setXEnd(Integer.MAX_VALUE);
                //抹掉其他横线
                List<TableLine.HorizonLine> newLastHorizonLine = new ArrayList<>();
                newLastHorizonLine.add(horizonLine);
                lastLineListMap.setValue(newLastHorizonLine);
            }

            tableYEnd = horizonList.get(0).getKey();
            tableYStart = horizonList.get(horizonList.size()-1).getKey();
        }
        if(!CollectionUtils.isEmpty(verticalLines)){
            //第一条竖线和最后一条竖线，人为使其扩展至页面最大值
            TableLine.VerticalLine firstVerticalLine = verticalLines.get(0);
            //todo，后续最好根据页面最大范围来设置
            firstVerticalLine.setYStart(-Integer.MAX_VALUE);
            firstVerticalLine.setYEnd(Integer.MAX_VALUE);
            double firstVerticalLineX = firstVerticalLine.getX();

            TableLine.VerticalLine lastVerticalLine = verticalLines.get(verticalLines.size()-1);
            //todo，后续最好根据页面最大范围来设置
            lastVerticalLine.setYStart(-Integer.MAX_VALUE);
            lastVerticalLine.setYEnd(Integer.MAX_VALUE);
            double lastVerticalLineX = lastVerticalLine.getX();

            //抹除与该两条线在同一x值位置的其他竖线
            List<TableLine.VerticalLine> newVerticalLines = new ArrayList<>();
            for(TableLine.VerticalLine verticalLine:verticalLines){
                double tmpX = verticalLine.getX();
                if(tmpX!=firstVerticalLineX&&tmpX!=lastVerticalLineX){
                    newVerticalLines.add(verticalLine);
                }
            }
            newVerticalLines.add(0,firstVerticalLine);
            newVerticalLines.add(lastVerticalLine);
            verticalLines = newVerticalLines;

            tableXStart = verticalLines.get(0).getX();
            tableXEnd = verticalLines.get(verticalLines.size() - 1).getX();
        }

        for(int i=0;i<horizonList.size()-1;i++){
            Double floorY = horizonList.get(i).getKey();
            List<TableLine.HorizonLine> floorLines = horizonList.get(i).getValue();
            Double bottomY = horizonList.get(i + 1).getKey();
            List<TableLine.HorizonLine> bottomLines = horizonList.get(i + 1).getValue();

            Set<Double> set = new HashSet<>();
            int pre=0;
            int pos=0;
            int size = verticalLines.size();
            boolean preFind = false;
            boolean posFind = false;
            int colCount = 0;
            boolean firstIn = true;
            for(;;){
                //找到一根穿过floorY和bottomY的线
                preFind = false;
                if(pos!=0){
                    pre = pos;
                    preFind = true;
                }else{
                    for(int j=pre;j<size;j++){
                        TableLine.VerticalLine tmp = verticalLines.get(pre);
                        double yStart = tmp.getYStart();
                        double yEnd = tmp.getYEnd();
                        if(yStart<bottomY && yEnd>floorY){
                            preFind = true;
                            pre = j;
                            break;
                        }
                    }
                }
                //再让pos找
                posFind = false;
                set.clear();
                for(pos=pre+1;pos<size;pos++){
                    TableLine.VerticalLine tmp = verticalLines.get(pos);
                    double yStart = tmp.getYStart();
                    double yEnd = tmp.getYEnd();

                    if(yStart<bottomY && yEnd>floorY){
                        posFind = true;
                        break;
                    }else if(yStart<floorY&&yStart>bottomY){
                        //上方穿过
                        set.add(tmp.getX());
                    }else if(yEnd>bottomY&&yEnd<floorY){
                        //下方穿过
                        set.add(tmp.getX());
                    }
                }
                if(preFind&&posFind){

                    double leftX = verticalLines.get(pre).getX();
                    double rightX = verticalLines.get(pos).getX();
                    for (TableLine.VerticalLine tmp : verticalLines) {
                        double x = tmp.getX();
                        if (x > leftX && x < rightX) {
                            set.add(x);
                        }
                    }

                    if(firstIn){
                        curRowIndex++;
                        firstIn = false;
                    }
                    colCount ++;
                    Cell cell = new Cell(leftX, rightX, floorY, bottomY);
                    cell.setColSpan(set.size()+1);
                    cell.setRowIndex(curRowIndex);
                    rowNum = Math.max(curRowIndex,rowNum);
                    colNum = Math.max(colCount,colNum);
                    cell.setColIndex(colCount);
                    //获得两个竖线中间的位置
                    TableLine.VerticalLine left = verticalLines.get(pre);
                    TableLine.VerticalLine right = verticalLines.get(pos);
                    double middle = (left.getX()+right.getX())/2;

                    if(isInLine(floorLines,middle)){
                        if(isInLine(bottomLines,middle)){
                            //上下都是封闭的
                            cell.setRowSpan(1);
                        }else{
                            //上方封闭，下方开放
                            cell.setRowSpanStatus(1);
                        }
                    }else{
                        if(isInLine(bottomLines,middle)){
                            //上方开放，下方封闭
                            cell.setRowSpanStatus(-1);
                        }else{
                            //上下都是开放的
                            cell.setRowSpanStatus(0);
                        }
                    }
                    list.add(cell);
                }else{
                    break;
                }
            }
        }

        /**---------------------向下合并需要合并的单元格------------------------------------------ */
        List<Cell> waitRowCombineCells = list.stream().filter(x -> x.getRowSpanStatus() != null).sorted((o1, o2) -> {
            Double xEnd1 = o1.getXEnd();
            Double xEnd2 = o2.getXEnd();
            Integer rowIndex1 = o1.getRowIndex();
            Integer rowIndex2 = o2.getRowIndex();
            if(xEnd1<xEnd2){
                return -1;
            }else{
                return rowIndex1 - rowIndex2;
            }
        }).collect(Collectors.toList());

        //将1，0，-1状态的Cell进行合并
        List<Cell> rowCombinedCell = new ArrayList<>();
        Cell cell = null;
        for(Cell c:waitRowCombineCells){
            if(cell==null){
                cell = c;
            }else{
                Double xEnd = cell.getXEnd();
                if(!xEnd.equals(c.getXEnd())){
                    //断开
                    rowCombinedCell.add(cell);
                    cell = c;
                }else{
                    if(c.getRowSpanStatus()==1){
                        //断开
                        rowCombinedCell.add(cell);
                        cell = c;
                    }else if(c.getRowSpanStatus()==0){
                        //合并
                        cell.setYEnd(c.getYEnd());
                        cell.setRowSpan((cell.getRowSpan()==null?1:cell.getRowSpan())+1);
                    }else{
                        //-1 合并并断开
                        cell.setYEnd(c.getYEnd());
                        cell.setRowSpan((cell.getRowSpan()==null?1:cell.getRowSpan())+1);
                        rowCombinedCell.add(cell);
                        cell = null;
                    }
                }

            }
        }
        if(cell!=null){
            rowCombinedCell.add(cell);
        }
        List<Cell> cellAll = list.stream().filter(x -> x.getRowSpanStatus() == null).collect(Collectors.toList());
        cellAll.addAll(rowCombinedCell);
        Collections.sort(cellAll);
        denseCols(cellAll);
        return new TableInfo(rowNum,colNum,tableXStart,tableYStart,tableXEnd,tableYEnd,cellAll);
    }

    private static boolean isInLine(List<TableLine.HorizonLine> lines,Double d){
        for(TableLine.HorizonLine l:lines){
            double xStart = l.getXStart();
            double xEnd = l.getXEnd();
            if(d>xStart&&d<xEnd){
                return true;
            }
        }
        return false;
    }


    /**
     * 让每行的col下标不会从除1外的其他数字开始
     * @param cells 已经排序好的列表
     */
    private static void denseCols(List<Cell> cells){
        int curRow = 0;
        int preCol = 0;
        for (Cell cell : cells) {
            Integer rowIndex = cell.getRowIndex();
            if (curRow == 0) {
                curRow = rowIndex;
                preCol = 1;
                cell.setColIndex(preCol);
            } else {
                if (rowIndex == curRow) {
                    //说明是某一行的延续
                    cell.setColIndex(++preCol);
                } else if (rowIndex > curRow) {
                    //说明某一行新起
                    curRow = rowIndex;
                    preCol = 1;
                    cell.setColIndex(preCol);
                }
            }
        }
    }

    //适当拉长竖线，确保该相交的地方相交
    private static void stretchVerticalLine(List<TableLine.VerticalLine> verticalLines){
        verticalLines.forEach(x->{
            x.setYStart(x.getYStart()-2);
            x.setYEnd(x.getYEnd()+2);
            x.setLength(x.getLength()+4);
        });
    }

    private static void stretchHorizonLine(List<TableLine.HorizonLine> horizonLines){
        horizonLines.forEach(x->{
            x.setXStart(x.getXStart()-2);
            x.setXEnd(x.getXEnd()+2);
            x.setLength(x.getLength()+4);
        });
    }

    private static void unifyVerticalLine(List<TableLine.VerticalLine> verticalLines){
        TreeSet<Double> treeSet = new TreeSet<>((Comparator<Double>) (o1, o2) -> {
            if (Math.abs(o1 - o2) <= 5.0d) {
                return 0;
            } else if (o1 - o2 > 5.0d) {
                return 1;
            } else {
                return -1;
            }
        });

        verticalLines.forEach(x->{
            treeSet.add(x.getX());
        });
        verticalLines.forEach(x->{
            double x1 = x.getX();
            for(Double d:treeSet){
                if(Math.abs(d-x1)<5.0d){
                    x.setX(d);
                    break;
                }
            }
        });
    }
    private static void unifyHorizonLine(List<TableLine.HorizonLine> horizonLines){
        TreeSet<Double> treeSet = new TreeSet<>((Comparator<Double>) (o1, o2) -> {
            if (Math.abs(o1 - o2) <= 5d) {
                return 0;
            } else if (o1 - o2 > 5d) {
                return 1;
            } else {
                return -1;
            }
        });
        horizonLines.forEach(x->{
            treeSet.add(x.getY());
        });
        horizonLines.forEach(x->{
            double y1 = x.getY();
            for(Double d:treeSet){
                if(Math.abs(d-y1)<5d){
                    x.setY(d);
                    break;
                }
            }
        });
    }
}
