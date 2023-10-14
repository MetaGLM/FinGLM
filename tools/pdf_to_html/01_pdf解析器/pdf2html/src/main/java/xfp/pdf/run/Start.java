package xfp.pdf.run;

import java.io.IOException;

public class Start {
    public static void main(String[] args) throws IOException {
        //    public static String inputAllPdfPath = "..\\..\\存放pdf";
        //
        //    public static String outputAllHtmlPath = "..\\..\\存放解析出的html";;
        //
        //    public static String output3TableCsvDir = "..\\..\\这里存放结果csv";
        //    //所有pdf转成的html的位置
        //
        //    //银行的pdf比较特殊，针对银行的pdf进行特殊提取，输出的银行年报的csv位置
        //    public static String outputBankReportCsvPath = "..\\..\\这里存放结果csv";
        String[] args1 = new String[]{args[0],args[1]};
        String[] args2 = new String[]{args[0],args[2]};
        String[] args3 = new String[]{args[1],args[2]};

        Pdf2html.pdf2html(args1);
        ExtractBankFinancialFromPDF.getBanCsv(args2);
        Extract3TableFromHtml.get3Table(args3);
    }


}
