package xfp.pdf.tools;

import com.google.gson.Gson;
import xfp.pdf.pojo.ExtractPojo;
import xfp.pdf.pojo.MarkPojo;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.util.stream.Collectors;


public class SettingReader {


    private static ExtractPojo docExtract;
    private static ExtractPojo msgExtract;
    private static ExtractPojo pdfExtract;

    private static MarkPojo docMark;
    private static MarkPojo msgMark;
    private static MarkPojo pdfMark;

    public static ExtractPojo getDocExtract() {
        if(docExtract==null){
            //读取resource下配置文件
            InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("extract_default/doc_extract.json");
            String result = new BufferedReader(new InputStreamReader(inputStream))
                    .lines().collect(Collectors.joining(System.lineSeparator()));
            Gson gson = new Gson();
            docExtract = gson.fromJson(result, ExtractPojo.class);
            try {
                inputStream.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return docExtract;
    }

    public static ExtractPojo getMsgExtract() {
        if(msgExtract==null){
            //读取resource下配置文件
            InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("extract_default/msg_extract.json");
            String result = new BufferedReader(new InputStreamReader(inputStream))
                    .lines().collect(Collectors.joining(System.lineSeparator()));
            Gson gson = new Gson();
            msgExtract = gson.fromJson(result, ExtractPojo.class);
            try {
                inputStream.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return msgExtract;
    }

    public static ExtractPojo getPdfExtract() {
        if(pdfExtract==null){
            //读取resource下配置文件
            InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("extract_default/pdf_extract.json");
            String result = new BufferedReader(new InputStreamReader(inputStream))
                    .lines().collect(Collectors.joining(System.lineSeparator()));
            Gson gson = new Gson();
            pdfExtract = gson.fromJson(result, ExtractPojo.class);
            try {
                inputStream.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return pdfExtract;
    }

    public static MarkPojo getDocMark() {
        if(docMark==null){
            //读取resource下配置文件
            InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("mark_default/doc_mark.json");
            String result = new BufferedReader(new InputStreamReader(inputStream))
                    .lines().collect(Collectors.joining(System.lineSeparator()));
            Gson gson = new Gson();
            docMark = gson.fromJson(result, MarkPojo.class);
            try {
                inputStream.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return docMark;
    }

    public static MarkPojo getMsgMark() {
        if(msgMark==null){
            //读取resource下配置文件
            InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("mark_default/msg_mark.json");
            String result = new BufferedReader(new InputStreamReader(inputStream))
                    .lines().collect(Collectors.joining(System.lineSeparator()));
            Gson gson = new Gson();
            msgMark = gson.fromJson(result, MarkPojo.class);
            try {
                inputStream.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return msgMark;
    }

    public static MarkPojo getPdfMark() {
        if(pdfMark==null){
            //读取resource下配置文件
            InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("mark_default/original/pdf_mark.json");
            String result = new BufferedReader(new InputStreamReader(inputStream))
                    .lines().collect(Collectors.joining(System.lineSeparator()));
            Gson gson = new Gson();
            pdfMark = gson.fromJson(result, MarkPojo.class);
            try {
                inputStream.close();
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
        return pdfMark;
    }

//    static {
//        //读取resource下配置文件
//        InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("./extract/doc_extract.json");
//        String result = new BufferedReader(new InputStreamReader(inputStream))
//                .lines().collect(Collectors.joining(System.lineSeparator()));
//        Gson gson = new Gson();
//        docExtract = gson.fromJson(result, ExtractPojo.class);
//        try {
//            inputStream.close();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//    }
//    static {
//        //读取resource下配置文件
//        InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("./extract/msg_extract.json");
//        String result = new BufferedReader(new InputStreamReader(inputStream))
//                .lines().collect(Collectors.joining(System.lineSeparator()));
//        Gson gson = new Gson();
//        msgExtract = gson.fromJson(result, ExtractPojo.class);
//        try {
//            inputStream.close();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//    }
//    static {
//        //读取resource下配置文件
//        InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("./extract/pdf_extract.json");
//        String result = new BufferedReader(new InputStreamReader(inputStream))
//                .lines().collect(Collectors.joining(System.lineSeparator()));
//        Gson gson = new Gson();
//        pdfExtract = gson.fromJson(result, ExtractPojo.class);
//        try {
//            inputStream.close();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//    }
//    static {
//        //读取resource下配置文件
//        InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("./mark/doc_mark.json");
//        String result = new BufferedReader(new InputStreamReader(inputStream))
//                .lines().collect(Collectors.joining(System.lineSeparator()));
//        Gson gson = new Gson();
//        docMark = gson.fromJson(result, MarkPojo.class);
//        try {
//            inputStream.close();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//    }
//    static {
//        //读取resource下配置文件
//        InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("./mark/msg_mark.json");
//        String result = new BufferedReader(new InputStreamReader(inputStream))
//                .lines().collect(Collectors.joining(System.lineSeparator()));
//        Gson gson = new Gson();
//        msgMark = gson.fromJson(result, MarkPojo.class);
//        try {
//            inputStream.close();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//    }
//    static {
//        //读取resource下配置文件
//        InputStream inputStream= SettingReader.class.getClassLoader().getResourceAsStream("./mark/pdf_mark.json");
//        String result = new BufferedReader(new InputStreamReader(inputStream))
//                .lines().collect(Collectors.joining(System.lineSeparator()));
//        Gson gson = new Gson();
//        pdfMark = gson.fromJson(result, MarkPojo.class);
//        try {
//            inputStream.close();
//        } catch (IOException e) {
//            e.printStackTrace();
//        }
//    }


}
