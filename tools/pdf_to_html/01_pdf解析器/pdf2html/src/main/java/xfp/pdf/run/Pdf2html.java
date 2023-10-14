package xfp.pdf.run;

import org.apache.pdfbox.pdmodel.PDDocument;
import xfp.pdf.arrange.MarkPdf;
import xfp.pdf.core.PdfParser;
import xfp.pdf.pojo.ContentPojo;
import xfp.pdf.tools.FileTool;

import java.io.File;
import java.io.IOException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;


public class Pdf2html {

    public static void pdf2html(String[] args){
        String inputAllPdfPath = "";
        String outputAllHtmlPath = "";
        if(args.length==2){
            inputAllPdfPath = args[0];
            outputAllHtmlPath = args[1];
        }else{
            inputAllPdfPath = Path.inputAllPdfPath;
            outputAllHtmlPath = Path.outputAllHtmlPath;
        }


        File file = new File(inputAllPdfPath);
        File[] files = file.listFiles();

        File file1 = new File(outputAllHtmlPath);
        File[] files2 = file1.listFiles();
        Set<String> set = new HashSet<>();
        if(files2!=null){
            for(File f:files2){
                set.add(f.getName().split("\\.")[1]);
            }
        }

        ExecutorService executor = Executors.newFixedThreadPool(16); // 创建一个线程池，这里的5表示最多同时运行5个线程

        for (File f : files) {
            String finalOutputAllHtmlPath = outputAllHtmlPath;
            executor.execute(() -> { // 提交一个任务给线程池
                PDDocument pdd = null;
                try {
                    String name = f.getName();
                    String namet = name.split("\\.")[1];
                    if(set.contains(namet)){
                        System.out.println("跳过 "+name);
                        return;
                    }
                    System.out.println("处理 "+name+" 中");
                    String htmlName = name.replaceAll("pdf","").replaceAll("PDF","")+"html";
                    File[] files1 = new File(finalOutputAllHtmlPath).listFiles();
                    for(File hf:files1){
                        if(hf.getName().equals(htmlName)){
                            return;
                        }
                    }
                    pdd = PDDocument.load(f);
                    ContentPojo contentPojo = PdfParser.parsingUnTaggedPdfWithTableDetection(pdd,false);
                    MarkPdf.markTitleSep(contentPojo);
                    FileTool.saveHTML(finalOutputAllHtmlPath, contentPojo, f.getAbsolutePath());
                } catch (IOException e) {
                    e.printStackTrace();
                }finally {
                    try {
                        if(pdd!=null){
                            pdd.close();
                        }
                    } catch (IOException e) {
                        throw new RuntimeException(e);
                    }
                }
            });
        }
        executor.shutdown();
    }

    public static void main(String[] args) throws IOException {

    }
}