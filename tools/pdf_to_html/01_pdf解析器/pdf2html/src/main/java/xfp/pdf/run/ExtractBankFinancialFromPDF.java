package xfp.pdf.run;

import org.apache.pdfbox.pdmodel.PDDocument;
import xfp.pdf.arrange.MarkPdf;
import xfp.pdf.core.PdfParser;
import xfp.pdf.pojo.ContentPojo;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.List;

public class ExtractBankFinancialFromPDF {

    public static void getBanCsv(String[] args) throws IOException{
        String inputFilePathDir = Path.inputAllPdfPath;
        String outputFilePathDir = Path.outputBankReportCsvPath;

        if(args.length==2){
            inputFilePathDir = args[0];
            outputFilePathDir = args[1];
        }


        File file = new File(inputFilePathDir);
        File[] files = file.listFiles();

        File outFile = new File(outputFilePathDir+"\\bank.csv");
        FileWriter fw = null;
        BufferedWriter bw = null;
        try {
            if(!outFile.exists()) {
                outFile.createNewFile();
            }
            fw = new FileWriter(outFile.getAbsoluteFile(), true);  //true续写新内容
            bw = new BufferedWriter(fw);
        } catch (Exception e) {
            e.printStackTrace();
        }


        for(File f:files){
            String name = f.getName();
            String compname = name.split("__")[1];
            if(!compname.contains("银行")){
                continue;
            }
            System.out.println("处理银行pdf "+compname+ " 中");
            PDDocument pdd = null;
            try {
                pdd = PDDocument.load(f);
                String bankBeanStr = parsingUnTaggedPdfWithTableDetectionAndPicture(pdd);
                String[] s = f.getName().split("__");
                String year = s[4];
                String src = s[5];
                String code = s[2];
                String bondname = s[3];
                bw.write(String.format("%s\001%s\001%s\001%s\001",year,src,code,bondname) +bankBeanStr+"\n");
                bw.flush();
            } catch (IOException e) {
                e.printStackTrace();
            }finally {
                try {
                    pdd.close();
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            }
        }
        bw.flush();
        bw.close();
    }



    private static class BankBean{
        public String s1;
        public String s2;
        public String s3;
        public String s4;
        public String s5;
        public String s6;
        public String s7;
        public String s8;
        public String s9;
        public String s10;
        @Override
        public String toString() {
            return String.format("%s\001%s\001%s\001%s\001%s\001%s\001%s\001%s\001%s\001%s",s1,s2,s3,s4,s5,s6,s7,s8,s9,s10);
        }
    }


    private static String parsingUnTaggedPdfWithTableDetectionAndPicture(PDDocument pdd) throws IOException {
        ContentPojo contentPojo = PdfParser.parsingUnTaggedPdfWithTableDetection(pdd,true);
        MarkPdf.markTitleSep(contentPojo);

        int unit = -1;
        BankBean bankBean = new BankBean();
        List<ContentPojo.contentElement> outList = contentPojo.getOutList();
        for(int i=0;i<outList.size();i++){
            ContentPojo.contentElement contentElement = outList.get(i);
            String text = contentElement.getText();
            if(text==null){
                continue;
            }
            String[] lines = text.split("\n");
            for(int j=0;j< lines.length;j++){
                String line = lines[j];
                if(line!=null && line.trim().startsWith("资产总计") && bankBean.s1==null){
                    for(int k=0;k<=200;k++){
                        if(i-k>=0){
                            ContentPojo.contentElement tmpE = outList.get(i-k);
                            if(tmpE.getText()==null){
                                continue;
                            }
                            if(tmpE.getText().contains("百万元")){
                                unit=1;
                                break;
                            }else if(tmpE.getText().contains("千元")){
                                unit=0;
                                break;
                            }else{
                                unit=-1;
                            }
                        }
                    }
                    String[] values = line.split(" ");
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s1 = String.format("%.2f",digit);
                            break;
                        }
                    }
                } else if (line!=null && line.trim().startsWith("负债合计") &&  bankBean.s2==null) {
                    String[] values = line.split(" ");
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s2 = String.format("%.2f",digit);
                            break;
                        }
                    }
                } else if (line!=null && line.trim().startsWith("股东权益合计") &&  bankBean.s3==null) {
                    String[] values = line.split(" ");
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s3 = String.format("%.2f",digit);
                            break;
                        }
                    }
                }else if (line!=null && line.trim().startsWith("利息收入") &&  bankBean.s4==null) {
                    String[] values = line.split(" ");
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null && digit>100){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s4 = String.format("%.2f",digit);
                            break;
                        }
                    }
                }else if (line!=null && line.trim().startsWith("利息支出") &&  bankBean.s5==null) {
                    String[] values = line.split(" ");
                    int count = 2;
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null && digit>100){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s5 = String.format("%.2f",digit);
                            break;
                        }
                    }
                } else if (line!=null &&  bankBean.s6==null && (line.trim().startsWith("营业收入合计") || startWith(line.trim(),"营业总收入",3))) {
                    String[] values = line.split(" ");
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s6 = String.format("%.2f",digit);
                            break;
                        }
                    }
                } else if (line!=null &&  bankBean.s7==null && (line.trim().startsWith("营业支出合计") || startWith(line.trim(),"营业总支出",3))) {
                    String[] values = line.split(" ");
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s7 = String.format("%.2f",digit);
                            break;
                        }
                    }
                }else if (line!=null && bankBean.s8==null && startWith(line.trim(),"营业利润",3)) {
                    String[] values = line.split(" ");
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s8 = String.format("%.2f",digit);
                            break;
                        }
                    }
                }else if (line!=null && bankBean.s9==null &&  startWith(line.trim(),"利润总额",3)) {
                    String[] values = line.split(" ");
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s9 = String.format("%.2f",digit);
                            break;
                        }
                    }
                }
                else if (line!=null && bankBean.s10==null && startWith(line.trim(),"净利润",3)) {
                    String[] values = line.split(" ");
                    for(String v:values){
                        String s = v.replaceAll(",", "");
                        Double digit = toDigit(s);
                        if(digit!=null){
                            if(unit==0){
                                digit = digit*1000;
                            }else if(unit==1){
                                digit = digit*1000000;
                            }
                            bankBean.s10 = String.format("%.2f",digit);
                            break;
                        }
                    }
                }

            }

        }
        return bankBean.toString();
    }

    private static Double toDigit(String text){
        String curText = text;
        if(text.startsWith("(")&&text.endsWith(")")){
            curText = text.replaceAll("\\(", "").replaceAll("\\)", "");
        }
        Double v = null;
        try {
            v = Double.parseDouble(curText);
        }catch (Exception e){
            return null;
        }
        return v;
    }

    private static boolean startWith(String text,String match,int i){
        if(text.length()<i){
            return false;
        }
        for(int j=1;j<=i;j++){
            String p = text.substring(j);
            if(p.startsWith(match)){
                return true;
            }
        }
        return false;
    }

    public static boolean testIsNumMethodThree(String str) {
        boolean flag = false;
        for (int i = 0; i < str.length(); i++) {
            char c = str.charAt(i);
            if (c > 48 && c < 57) {
                flag = true;
            }
        }
        return flag;
    }
}
