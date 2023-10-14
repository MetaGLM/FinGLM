package xfp.pdf.table;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.ToString;


public class TableLine {

    @Data
    @ToString
    @NoArgsConstructor
    public static class VerticalLine implements Comparable<VerticalLine>{
        public double x;
        public double yStart;
        public double yEnd;
        public double length;
        public VerticalLine(double x,double yStart,double yEnd){
            this.x = x;
            this.yStart = yStart;
            this.yEnd = yEnd;
            this.length = yEnd - yStart;
        }
        @Override
        public int compareTo(VerticalLine v) {
            //x较小的排前，yStart较大的排前
            double x = v.getX();
            double yStart = v.getYStart();
            if(this.x<x){
                return -1;
            }else if(this.x>x){
                return 1;
            }else{
                return -Double.compare(yStart, this.yStart);
            }
        }
    }

    @Data
    @ToString
    @NoArgsConstructor
    public static class HorizonLine implements Comparable<HorizonLine>{
        public double y;
        public double xStart;
        public double xEnd;
        public double length;
        public HorizonLine(double y,double xStart,double xEnd){
            this.y = y;
            this.xStart = xStart;
            this.xEnd = xEnd;
            this.length = xEnd - xStart;
        }
        @Override
        public int compareTo(HorizonLine h) {
            //y较大的排前，xstart较小的排前
            double y = h.getY();
            double xStart = h.getXStart();
            if(this.y>y){
                return -1;
            }else if(this.y<y){
                return 1;
            }else{
                return Double.compare(this.xStart, xStart);
            }
        }
    }


    public static VerticalLine connectVLine(VerticalLine v1,VerticalLine v2){
        return new VerticalLine(v1.getX(), v1.getYStart(), Math.max(v1.getYEnd(),v2.getYEnd()));
    }

    public static HorizonLine connectHLine(HorizonLine h1,HorizonLine h2){
        return new HorizonLine(h1.getY(),h1.getXStart(),Math.max(h1.getXEnd(),h2.getXEnd()));
    }

}
