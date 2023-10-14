package xfp.pdf.run;

import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import xfp.pdf.pojo.Tu;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class Extract3TableFromHtml {


    public static String handlerValue(String srcValue,int unit){
        String value = srcValue.replaceAll(" ", "").replaceAll(",", "").replaceAll("，", "").
                replaceAll("\r", "").replaceAll("\n", "");
        Double v = 0d;
        try{
            if(value.startsWith("(")){
                value = value.replaceAll("\\(","").replaceAll("\\)","");
                value = "-"+value;
            }
            v = Double.parseDouble(value);
        }catch (Exception e){

        }
        switch (unit){
            case 0:return String.format("%.2f",v);
            case 1:return String.format("%.2f",v*1000);
            case 2:return String.format("%.2f",v*10000);
            case 3:return String.format("%.2f",v*100000);
            case 4:return String.format("%.2f",v*1000000);
        }
        return "0";
    }

    public static Tu.Tuple2<Integer,String> extractField(String srcName, String srcValue, List<String> rules,int unit){
        srcName = srcName.replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");

        for(int i=0;i<rules.size();i++){
            String rule = rules.get(i);
            if(rule.contains("__")){
                String[] strs = rule.split("__");
                for(String str:strs){
                    if(str.contains("_")){
                        String[] tstrs = str.split("_");
                        boolean flag = true;
                        for(String tstr:tstrs){
                            if(tstr.startsWith("<")){
                                tstr = tstr.substring(1,tstr.length()-1);
                                if(srcName.contains(tstr)){
                                    flag = false;
                                    break;
                                }
                            }else if(tstr.startsWith("^")){
                                tstr = tstr.substring(1);
                                if(!srcName.startsWith(tstr)){
                                    flag = false;
                                    break;
                                }
                            }
                            else if(!srcName.contains(tstr)){
                                flag = false;
                                break;
                            }
                        }
                        if(flag){
                            return new Tu.Tuple2<>(i,handlerValue(srcValue,unit));
                        }
                    }else{
                        if(srcName.contains(str) && !srcName.contains("融资")){
                            return new Tu.Tuple2<>(i,handlerValue(srcValue,unit));
                        }
                    }



                }
            }else if(rule.contains("_")){
                String[] strs = rule.split("_");
                boolean flag = true;
                for(String str:strs){
                    if(str.startsWith("<")){
                        str = str.substring(1,str.length()-1);
                        if(srcName.contains(str)){
                           flag = false;
                           break;
                        }
                    }else if(str.startsWith("^")){
                        str = str.substring(1);
                        if(!srcName.startsWith(str)){
                            flag = false;
                            break;
                        }
                    }
                    else if(!srcName.contains(str)){
                        flag = false;
                        break;
                    }
                }
                if(flag){
                    return new Tu.Tuple2<>(i,handlerValue(srcValue,unit));
                }
            }else {
                if (rule.startsWith("^")) {
                    rule = rule.substring(1);
                    if (srcName.startsWith(rule)) {
                        return new Tu.Tuple2<>(i, handlerValue(srcValue, unit));
                    }
                }else{
                    if (srcName.contains(rule)) {
                        return new Tu.Tuple2<>(i, handlerValue(srcValue, unit));
                    }
                }
            }
        }
        return null;
    }

    public static FileWriter balanceWriter = null;
    public static FileWriter profitWriter = null;
    public static FileWriter cashflowWriter = null;

    static {
        File balanceFile = new File(Path.output3TableCsvDir+"\\balance.csv");
        File profitFile = new File(Path.output3TableCsvDir+"\\profit.csv");
        File cashflowFile = new File(Path.output3TableCsvDir+"\\cashflow.csv");

        try {
            balanceWriter = new FileWriter(balanceFile);
            profitWriter = new FileWriter(profitFile);
            cashflowWriter = new FileWriter(cashflowFile);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }



    public static  void text2File(final String strFilename, final String strBuffer)
    {
        try
        {
            // 创建文件对象
            File fileText = new File(strFilename);
            // 向文件写入对象写入信息
            FileWriter fileWriter = new FileWriter(fileText);

            // 写文件
            fileWriter.write(strBuffer);
            // 关闭
            fileWriter.close();
        }
        catch (IOException e)
        {
            //
            e.printStackTrace();
        }
    }

    public static void handlerHtml(File file,Boolean endFlag) throws IOException {
//        File file =new File("D:\\project\\opensource\\FinanceBestChatGLM\\data_extract\\数据处理过程目录\\html结果\\2022-04-30__创新医疗管理股份有限公司__002173__创新医疗__2021年__年度报告.html");
        Document document = Jsoup.parse(file, "utf-8");
        String name = file.getName();


        int condition = 0;
        //0 -> 元 1 -> 千 2 -> 万 3 -> 十万 4 -> 百万
        int unit = 0;
        Integer year = Integer.parseInt(file.getName().split("__")[4].substring(0, 4));
        String chineseYear = "";
        if(year==2019){
            chineseYear = "二零一九";
        }else if(year==2021){
            chineseYear = "二零二一";
        }else if(year==2020){
            chineseYear = "二零二零";
        }
        List<String> yearList = new ArrayList<>();
        yearList.add("本期");
        yearList.add("本年");
        yearList.add(chineseYear);
        yearList.add(String.valueOf(year));



        List<String> balanceRules = new ArrayList<>();
        balanceRules.add("货币资金");
        balanceRules.add("应收票据");
        balanceRules.add("应收利息");
        balanceRules.add("应收账款__应收款项");
        balanceRules.add("应收款项融资");
        balanceRules.add("其他应收款");
        balanceRules.add("预付账款__预付款项");
        balanceRules.add("存货");
        balanceRules.add("一年内到期的非流动资产");
        balanceRules.add("其他流动资产");
        balanceRules.add("投资性房地产");
        balanceRules.add("长期股权投资");
        balanceRules.add("长期应收款");
        balanceRules.add("固定资产");
        balanceRules.add("工程物资");
        balanceRules.add("在建工程");
        balanceRules.add("无形资产");

        balanceRules.add("商誉");
        balanceRules.add("长期待摊费用");
        balanceRules.add("递延所得税资产");
        balanceRules.add("其他非流动资产");
        balanceRules.add("短期借款");
        balanceRules.add("应付票据");
        balanceRules.add("应付账款");
        balanceRules.add("预收款项");
        balanceRules.add("应付职工薪酬_<长期>");
        balanceRules.add("应付股利");
        balanceRules.add("应交税费");
        balanceRules.add("应付利息");
        balanceRules.add("其他应付款");
        balanceRules.add("一年内到期的非流动负债");
        balanceRules.add("其他流动负债");
        balanceRules.add("长期借款");

        balanceRules.add("应付债券");
        balanceRules.add("长期应付款");
        balanceRules.add("预计负债");
        balanceRules.add("递延所得税负债");
        balanceRules.add("其他非流动负债");
        balanceRules.add("实收资本_^股本");
        balanceRules.add("资本公积");
        balanceRules.add("盈余公积");
        balanceRules.add("未分配利润");
        balanceRules.add("其他综合收益");
        balanceRules.add("长期应付职工薪酬");
        balanceRules.add("长期递延收益");
        balanceRules.add("合同资产");
        balanceRules.add("其他非流动金融资产");
        balanceRules.add("应付票据及应付账款");
        balanceRules.add("合同负债");

        balanceRules.add("其他权益工具投资");
        balanceRules.add("负债_合计_<流动>");
        balanceRules.add("资产_总计");
        balanceRules.add("^所有者权益_合计__^股东权益_合计");
//        balanceRules.add("^股东权益_合计");

        balanceRules.add("衍生金融资产");

        balanceRules.add("流动资产_合计_<非>");
        balanceRules.add("非流动资产_合计");
        balanceRules.add("流动负债_合计_<非>");
        balanceRules.add("非流动负债_合计");




        List<String> balanceResultList = new ArrayList<>();
        for(String str:balanceRules){
            balanceResultList.add(null);
        }

        List<String> profitRules = new ArrayList<>();
        profitRules.add("营业总收入");
        profitRules.add("营业收入__主营业务收入");
        profitRules.add("其他业务收入");
        profitRules.add("营业总成本");
        profitRules.add("营业成本__主营业务成本");
        profitRules.add("利息支出");
        profitRules.add("其他业务成本");
        profitRules.add("税金及附加");
        profitRules.add("销售费用");
        profitRules.add("管理费用");
        profitRules.add("研发费用");
        profitRules.add("财务费用");
        profitRules.add("利息费用");
        profitRules.add("利息收入");
        profitRules.add("^公允价值变动收益");
        profitRules.add("^投资收益");
        profitRules.add("营业利润");
        profitRules.add("营业外收入");
        profitRules.add("营业外支出");
        profitRules.add("利润总额");
        profitRules.add("所得税费用");
        profitRules.add("净利润");
        profitRules.add("其他收益");
        profitRules.add("综合收益总额");
        profitRules.add("基本每股收益");
        profitRules.add("稀释每股收益");

        List<String> profitResultList = new ArrayList<>();
        for(String str:profitRules){
            profitResultList.add(null);
        }

        List<String> cashFlowRules = new ArrayList<>();
        cashFlowRules.add("提供劳务收到的现金");
        cashFlowRules.add("收到的税费返还");
        cashFlowRules.add("收到其他_经营活动有关的现金");
        cashFlowRules.add("接受劳务支付的现金");
        cashFlowRules.add("支付给_为职工支付的现金");
        cashFlowRules.add("支付的各项税费");
        cashFlowRules.add("支付其他_经营活动有关的现金");
        cashFlowRules.add("经营活动_产生的现金流量净额");
        cashFlowRules.add("收回投资_收到的现金");
        cashFlowRules.add("取得投资收益_收到的现金");
        cashFlowRules.add("其他长期资产_收回_净额");
        cashFlowRules.add("处置子公司_其他营业单位_收到_净额");
        cashFlowRules.add("其他长期资产_支付_现金");
        cashFlowRules.add("投资_支付的现金");
        cashFlowRules.add("支付其他_投资活动有关的现金");
        cashFlowRules.add("投资活动产生的现金流量净额");

        cashFlowRules.add("吸收投资_收到的现金");
        cashFlowRules.add("取得借款_收到的现金");
        cashFlowRules.add("偿还债务_支付的现金");
        cashFlowRules.add("利润或偿付利息_支付的现金");
        cashFlowRules.add("筹资活动产生_现金流量净额");
        cashFlowRules.add("汇率变动_现金及现金等价物的影响");
        cashFlowRules.add("期初现金_现金等价物余额");
        cashFlowRules.add("期末现金_现金等价物余额");


        List<String> cashFlowResultList = new ArrayList<>();
        for(String str:cashFlowRules){
            cashFlowResultList.add(null);
        }

        boolean findBalanceTable = false;
        int finalColumn1 = -1;
        int column1 = -1;
        boolean findProfitTable =false;
        int finalColumn2 = -1;
        int column2 = -1;
        boolean findCashFlowTable =false;
        int finalColumn3 = -1;
        int column3 = -1;

        boolean countFlag = false;
        int countP = 0;

        int tolerateP = 0;
        Elements es = document.select("body");
        for (Element element : es) {
            Elements children = element.children();
            a:for(int k=0;k<children.size();k++){
                Element child = children.get(k);
                String text = child.text();
                if(condition == 0 && text.contains("财务报表")  && text.length()<10){
                    condition = 1;
                    continue;
                }else if(condition==1){
//                    if("p".equals(child.tagName())||"h".equals(child.tagName())){
//                        //单位
//                        String tmpText = child.text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");;
//                        if(tmpText.contains("千")){
//                            unit = 1;
//                        }else if(tmpText.contains("百万")){
//                            unit = 4;
//                        }
//                    }

                    if("p".equals(child.tagName())||"h".equals(child.tagName())){
                        tolerateP++;
                        if(tolerateP==10){
                            condition=0;
                            tolerateP=0;
                            continue;
                        }
                    }
                    if(text.contains("资产负债表")){
                        condition = 2;
                    }

                    continue;
                }else if(condition==2){
                    if(("p".equals(child.tagName())||"h".equals(child.tagName())) && findBalanceTable ){
                        //单位
                        String tmpText = child.text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");;
                        if(tmpText.contains("千")){
                            unit = 1;
                        }else if(tmpText.contains("百万")){
                            unit = 4;
                        }else if(tmpText.contains("十万")){
                            unit = 3;
                        }else if(tmpText.contains("万")){
                            unit = 2;
                        }
                    }
                    if("table".equals(child.tagName())){
                        Elements trs = child.select("tr");
                        //表格第一行
                        if(trs.size()>=1 && finalColumn1==-1){
                            Element tr0 = trs.get(0);
                            Elements tr0_tds = tr0.select("td");
                            List<Integer> indexes = new ArrayList<>();
                            List<String> matchText = new ArrayList<>();
                            for(int i=0;i<tr0_tds.size();i++){
                                String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                for(String yearStr:yearList){
                                    if(tr0_td_text.contains(yearStr)){
                                        matchText.add(tr0_td_text);
                                        indexes.add(i);
                                        break;
                                    }
                                }

                            }
                            if(matchText.size()>1){
                                //看谁有合并
                                for(int i=0;i<matchText.size();i++){
                                    if(matchText.get(i).contains("合并")){
                                        column1 = indexes.get(i);
                                    }
                                }
                                //实在没有就取第一个
                                if(column2==-1){
                                    column1 = indexes.get(0);
                                }
                            }else if(matchText.size()==1){
                                column1 = indexes.get(0);
                            }else if(matchText.size()==0){
                                //没有匹配到的，说明可能在第二行
                                if(trs.size()>=2 && column1==-1){
                                    tr0 = trs.get(1);
                                    tr0_tds = tr0.select("td");
                                    indexes = new ArrayList<>();
                                    matchText = new ArrayList<>();
                                    for(int i=0;i<tr0_tds.size();i++){
                                        String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                        for(String yearStr:yearList){
                                            if(tr0_td_text.contains(yearStr)){
                                                matchText.add(tr0_td_text);
                                                indexes.add(i);
                                                break;
                                            }
                                        }

                                    }
                                    if(matchText.size()>1){
                                        //看谁有合并
                                        for(int i=0;i<matchText.size();i++){
                                            if(matchText.get(i).contains("合并")){
                                                column1 = indexes.get(i);
                                            }
                                        }
                                        //实在没有就取第一个
                                        if(column1==-1){
                                            column1 = indexes.get(0);
                                        }
                                    }else if(matchText.size()==1){
                                        column1 = indexes.get(0);
                                    }
                                }
                            }
                            if(findBalanceTable){
                                finalColumn1 = column1;
                            }
                        }
                        int matchCount = 0;
                        for(int i=0;i<trs.size();i++){
                            Element tri = trs.get(i);
                            Elements tri_tds = tri.select("td");
                            if(column1==-1||column1==0){
                                if(tri_tds.size()==3){
                                    column1=1;
                                }else if(tri_tds.size()==4){
                                    column1=2;
                                }
                            }
                            if(column1!=-1 && tri_tds.size()>column1 && tri_tds.size()>=3){
                                String srcValue = tri_tds.get(column1).text();
                                String srcName1 = tri_tds.get(0).text();
                                Tu.Tuple2<Integer, String> tmpT = extractField(srcName1, srcValue, balanceRules, unit);
                                if(tmpT==null){
                                    String srcName2 = tri_tds.get(1).text();
                                    tmpT = extractField(srcName2, srcValue, balanceRules, unit);
                                }
                                if(tmpT!=null){
                                    matchCount++;
                                    if(!findBalanceTable&&matchCount>=3){
                                        findBalanceTable = true;
                                        k = Math.max(0,k-5);
                                        continue a;
                                    }
                                    if(findBalanceTable && balanceResultList.get(tmpT.getKey())==null){
                                        balanceResultList.set(tmpT.getKey(),tmpT.getValue());
                                    }
                                }
                            }

                        }

                    }else if("p".equals(child.tagName())||"h".equals(child.tagName())){
                        String curText = child.text();
                        if(curText.contains("利润表")){
                            condition = 3;
                            continue;
                        }
                    }
                }else if(condition==3){
                    if("table".equals(child.tagName())){
                        Elements trs = child.select("tr");
                        //表格第一行
                        if(trs.size()>=1 && finalColumn2==-1){
                            Element tr0 = trs.get(0);
                            Elements tr0_tds = tr0.select("td");
                            List<Integer> indexes = new ArrayList<>();
                            List<String> matchText = new ArrayList<>();
                            for(int i=0;i<tr0_tds.size();i++){
                                String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                for(String yearStr:yearList){
                                    if(tr0_td_text.contains(yearStr)){
                                        matchText.add(tr0_td_text);
                                        indexes.add(i);
                                        break;
                                    }
                                }
                            }
                            if(matchText.size()>1){
                                //看谁有合并
                                for(int i=0;i<matchText.size();i++){
                                    if(matchText.get(i).contains("合并")){
                                        column2 = indexes.get(i);
                                    }
                                }
                                //实在没有就取第一个
                                if(column2==-1){
                                    column2 = indexes.get(0);
                                }
                            }else if(matchText.size()==1){
                                column2 = indexes.get(0);
                            }else if(matchText.size()==0){
                                //没有匹配到的，说明可能在第二行
                                if(trs.size()>=2 && column2==-1){
                                    tr0 = trs.get(1);
                                    tr0_tds = tr0.select("td");
                                    indexes = new ArrayList<>();
                                    matchText = new ArrayList<>();
                                    for(int i=0;i<tr0_tds.size();i++){
                                        String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                        for(String yearStr:yearList){
                                            if(tr0_td_text.contains(yearStr)){
                                                matchText.add(tr0_td_text);
                                                indexes.add(i);
                                                break;
                                            }
                                        }

                                    }
                                    if(matchText.size()>1){
                                        //看谁有合并
                                        for(int i=0;i<matchText.size();i++){
                                            if(matchText.get(i).contains("合并")){
                                                column2 = indexes.get(i);
                                            }
                                        }
                                        //实在没有就取第一个
                                        if(column2==-1){
                                            column2 = indexes.get(0);
                                        }
                                    }else if(matchText.size()==1){
                                        column2 = indexes.get(0);
                                    }
                                }
                            }
                            if(findProfitTable){
                                finalColumn2 = column2;
                            }
                        }
                        int matchCount = 0;
                        for(int i=0;i<trs.size();i++){
                            Element tri = trs.get(i);
                            Elements tri_tds = tri.select("td");
                            if(column2==-1||column2==0){
                                if(tri_tds.size()==3){
                                    column2=1;
                                }else if(tri_tds.size()==4){
                                    column2=2;
                                }
                            }
                            if(column2!=-1 && tri_tds.size()>column2 && tri_tds.size()>=3){
                                String srcValue = tri_tds.get(column2).text();
                                String srcName1 = tri_tds.get(0).text();
                                Tu.Tuple2<Integer, String> tmpT = extractField(srcName1, srcValue, profitRules, unit);
                                if(tmpT==null){
                                    String srcName2 = tri_tds.get(1).text();
                                    tmpT = extractField(srcName2, srcValue, profitRules, unit);
                                }
                                if(tmpT!=null){
                                    matchCount++;
                                    if(!findProfitTable&&matchCount>=3){
                                        findProfitTable = true;
                                        k = Math.max(0,k-5);
                                        continue a;
                                    }
                                    if(findProfitTable && profitResultList.get(tmpT.getKey())==null){
                                        profitResultList.set(tmpT.getKey(),tmpT.getValue());
                                    }
                                }
                            }

                        }

                    }else if("p".equals(child.tagName())||"h".equals(child.tagName())){
                        String curText = child.text();
                        if(curText.contains("现金流量表")){
                            condition = 4;
                            continue;
                        }
                    }
                }else if(condition==4){
                    if(findCashFlowTable && countP>=4){
                        break;
                    }
                    if("table".equals(child.tagName())){
                        Elements trs = child.select("tr");
                        //表格第一行
                        if(trs.size()>=1 && finalColumn3==-1){
                            Element tr0 = trs.get(0);
                            Elements tr0_tds = tr0.select("td");
                            List<Integer> indexes = new ArrayList<>();
                            List<String> matchText = new ArrayList<>();
                            for(int i=0;i<tr0_tds.size();i++){
                                String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                for(String yearStr:yearList){
                                    if(tr0_td_text.contains(yearStr)){
                                        matchText.add(tr0_td_text);
                                        indexes.add(i);
                                        break;
                                    }
                                }
                            }
                            if(matchText.size()>1){
                                //看谁有合并
                                for(int i=0;i<matchText.size();i++){
                                    if(matchText.get(i).contains("合并")){
                                        column3 = indexes.get(i);
                                    }
                                }
                                //实在没有就取第一个
                                if(column3==-1){
                                    column3 = indexes.get(0);
                                }
                            }else if(matchText.size()==1){
                                column3 = indexes.get(0);
                            }else if(matchText.size()==0){
                                //没有匹配到的，说明可能在第二行
                                if(trs.size()>=2 && column3==-1){
                                    tr0 = trs.get(1);
                                    tr0_tds = tr0.select("td");
                                    indexes = new ArrayList<>();
                                    matchText = new ArrayList<>();
                                    for(int i=0;i<tr0_tds.size();i++){
                                        String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                        for(String yearStr:yearList){
                                            if(tr0_td_text.contains(yearStr)){
                                                matchText.add(tr0_td_text);
                                                indexes.add(i);
                                                break;
                                            }
                                        }

                                    }
                                    if(matchText.size()>1){
                                        //看谁有合并
                                        for(int i=0;i<matchText.size();i++){
                                            if(matchText.get(i).contains("合并")){
                                                column3 = indexes.get(i);
                                            }
                                        }
                                        //实在没有就取第一个
                                        if(column3==-1){
                                            column3 = indexes.get(0);
                                        }
                                    }else if(matchText.size()==1){
                                        column3 = indexes.get(0);
                                    }
                                }
                            }
                            if(findCashFlowTable){
                                finalColumn3 = column3;
                            }

                        }
                        int matchCount=0;
                        for(int i=0;i<trs.size();i++){
                            Element tri = trs.get(i);
                            Elements tri_tds = tri.select("td");
                            if(column3==-1||column3==0){
                                if(tri_tds.size()==3){
                                    column3=1;
                                }else if(tri_tds.size()==4){
                                    column3=2;
                                }
                            }
                            if(column3!=-1 && tri_tds.size()>column3 && tri_tds.size()>=3){
                                String srcValue = tri_tds.get(column3).text();
                                String srcName1 = tri_tds.get(0).text();
                                Tu.Tuple2<Integer, String> tmpT = extractField(srcName1, srcValue, cashFlowRules, unit);
                                if(tmpT==null){
                                    String srcName2 = tri_tds.get(1).text();
                                    tmpT = extractField(srcName2, srcValue, cashFlowRules, unit);
                                }
                                if(tmpT!=null){
                                    matchCount++;
                                    if(!findCashFlowTable&&matchCount>=3){
                                        findCashFlowTable = true;
                                        k = Math.max(0,k-5);
                                        continue a;
                                    }
                                    if(findProfitTable && cashFlowResultList.get(tmpT.getKey())==null){
                                        cashFlowResultList.set(tmpT.getKey(),tmpT.getValue());
                                    }
                                }
                            }

                        }
                        countFlag = true;

                    }
                    if(countFlag){
                        if(!"table".equals(child.tagName())){
                            countP++;
                        }
                    }
                }
            }


            //遍历所有表格暴力提取，表本身的特性提取




//            System.out.printf("%s\t%s\n" ,element.html() ,element.val());
        }
        //查看货币资金项有没有值，没有的话开始暴力搜索
        //搜索所有的表格，第一列包含流动资产，货币资金，应收账款三项的认为是资产负债表，然后重启有限状态机
        if(condition==0||balanceResultList.get(0)==null){
            condition = 0;
//            finalColumn1 =-1;
            column1 = -1;
//            finalColumn2 =-1;
            column2 = -1;
//            finalColumn3 =-1;
            column3 = -1;

//            findBalanceTable = false;
//            findProfitTable = false;
//            findCashFlowTable = false;


            countFlag = false;
            countP = 0;



            for (Element element : es) {
                Elements children = element.children();
                for(int j=0;j<children.size();j++){
                    Element child = children.get(j);
                    String text = child.text();
                    if(condition ==0 && child.tagName().equals("table")){
                        Elements trs = child.select("tr");
                        boolean tmpFlag1 = false;
                        boolean tmpFlag2 = false;
                        boolean tmpFlag3 = false;
                        for(Element e:trs){
                            Elements tds = e.select("td");
                            if(tds.size()>=1){
                                String fieldName = tds.get(0).text();
                                if(fieldName.contains("流动资产")){
                                    tmpFlag1 = true;
                                }else if(fieldName.contains("货币资金")){
                                    tmpFlag2 = true;
                                }else if(fieldName.contains("应收账款")){
                                    tmpFlag3 = true;
                                }
                            }
                        }
                        if(tmpFlag1&&tmpFlag2&&tmpFlag3){
                            condition =1;
                            //往回退10行，获得一些基础信息
                            if(j-10>=0){
                                j = j-10;
                            }
                        }
                        continue;
                    }else if(condition==1){
                        if("p".equals(child.tagName())||"h".equals(child.tagName())){
                            //单位
                            String tmpText = child.text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");;
                            if(tmpText.contains("千")){
                                unit = 1;
                            }else if(tmpText.contains("百万")){
                                unit = 4;
                            }else if(tmpText.contains("十万")){
                                unit = 3;
                            }else if(tmpText.contains("万")){
                                unit = 2;
                            }
                        }
                        if(text.contains("资产负债表")){
                            condition = 2;
                        }
                        continue;
                    }else if(condition==2){
                        if("p".equals(child.tagName())||"h".equals(child.tagName())){
                            //单位
                            String tmpText = child.text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");;
                            if(tmpText.contains("千")){
                                unit = 1;
                            }else if(tmpText.contains("百万")){
                                unit = 4;
                            }else if(tmpText.contains("十万")){
                                unit = 3;
                            }else if(tmpText.contains("万")){
                                unit = 2;
                            }
                        }
                        if("table".equals(child.tagName())){
                            Elements trs = child.select("tr");
                            //表格第一行
                            if(trs.size()>=1 && column1==-1){
                                Element tr0 = trs.get(0);
                                Elements tr0_tds = tr0.select("td");
                                List<Integer> indexes = new ArrayList<>();
                                List<String> matchText = new ArrayList<>();
                                for(int i=0;i<tr0_tds.size();i++){
                                    String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                    for(String yearStr:yearList){
                                        if(tr0_td_text.contains(yearStr)){
                                            matchText.add(tr0_td_text);
                                            indexes.add(i);
                                            break;
                                        }
                                    }
                                }
                                if(matchText.size()>1){
                                    //看谁有合并
                                    for(int i=0;i<matchText.size();i++){
                                        if(matchText.get(i).contains("合并")){
                                            column1 = indexes.get(i);
                                        }
                                    }
                                    //实在没有就取第一个
                                    if(column1==-1){
                                        column1 = indexes.get(0);
                                    }
                                }else if(matchText.size()==1){
                                    column1 = indexes.get(0);
                                }else if(matchText.size()==0){
                                    //没有匹配到的，说明可能在第二行
                                    if(trs.size()>=2 && column1==-1){
                                        tr0 = trs.get(1);
                                        tr0_tds = tr0.select("td");
                                        indexes = new ArrayList<>();
                                        matchText = new ArrayList<>();
                                        for(int i=0;i<tr0_tds.size();i++){
                                            String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                            for(String yearStr:yearList){
                                                if(tr0_td_text.contains(yearStr)){
                                                    matchText.add(tr0_td_text);
                                                    indexes.add(i);
                                                    break;
                                                }
                                            }

                                        }
                                        if(matchText.size()>1){
                                            //看谁有合并
                                            for(int i=0;i<matchText.size();i++){
                                                if(matchText.get(i).contains("合并")){
                                                    column1 = indexes.get(i);
                                                }
                                            }
                                            //实在没有就取第一个
                                            if(column1==-1){
                                                column1 = indexes.get(0);
                                            }
                                        }else if(matchText.size()==1){
                                            column1 = indexes.get(0);
                                        }
                                    }
                                }
                            }
                            for(int i=0;i<trs.size();i++){
                                Element tri = trs.get(i);
                                Elements tri_tds = tri.select("td");
                                if(column1==-1||column1==0){
                                    if(tri_tds.size()==3){
                                        column1=1;
                                    }else if(tri_tds.size()==4){
                                        column1=2;
                                    }
                                }
                                if(column1!=-1 && tri_tds.size()>column1 && tri_tds.size()>=3){
                                    String srcValue = tri_tds.get(column1).text();
                                    String srcName1 = tri_tds.get(0).text();
                                    Tu.Tuple2<Integer, String> tmpT = extractField(srcName1, srcValue, balanceRules, unit);
                                    if(tmpT==null){
                                        String srcName2 = tri_tds.get(1).text();
                                        tmpT = extractField(srcName2, srcValue, balanceRules, unit);
                                    }
                                    if(tmpT!=null){
                                        if(balanceResultList.get(tmpT.getKey())==null){
                                            balanceResultList.set(tmpT.getKey(),tmpT.getValue());
                                        }
                                    }
                                }

                            }

                        }else if("p".equals(child.tagName())||"h".equals(child.tagName())){
                            String curText = child.text();
                            if(curText.contains("利润表")){
                                condition = 3;
                                continue;
                            }
                        }
                    }else if(condition==3){
                        if("table".equals(child.tagName())){
                            Elements trs = child.select("tr");
                            //表格第一行
                            if(trs.size()>=1 && column2==-1){
                                Element tr0 = trs.get(0);
                                Elements tr0_tds = tr0.select("td");
                                List<Integer> indexes = new ArrayList<>();
                                List<String> matchText = new ArrayList<>();
                                for(int i=0;i<tr0_tds.size();i++){
                                    String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                    for(String yearStr:yearList){
                                        if(tr0_td_text.contains(yearStr)){
                                            matchText.add(tr0_td_text);
                                            indexes.add(i);
                                            break;
                                        }
                                    }
                                }
                                if(matchText.size()>1){
                                    //看谁有合并
                                    for(int i=0;i<matchText.size();i++){
                                        if(matchText.get(i).contains("合并")){
                                            column2 = indexes.get(i);
                                        }
                                    }
                                    //实在没有就取第一个
                                    if(column2==-1){
                                        column2 = indexes.get(0);
                                    }
                                }else if(matchText.size()==1){
                                    column2 = indexes.get(0);
                                }else if(matchText.size()==0){
                                    //没有匹配到的，说明可能在第二行
                                    if(trs.size()>=2 && column2==-1){
                                        tr0 = trs.get(1);
                                        tr0_tds = tr0.select("td");
                                        indexes = new ArrayList<>();
                                        matchText = new ArrayList<>();
                                        for(int i=0;i<tr0_tds.size();i++){
                                            String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                            for(String yearStr:yearList){
                                                if(tr0_td_text.contains(yearStr)){
                                                    matchText.add(tr0_td_text);
                                                    indexes.add(i);
                                                    break;
                                                }
                                            }

                                        }
                                        if(matchText.size()>1){
                                            //看谁有合并
                                            for(int i=0;i<matchText.size();i++){
                                                if(matchText.get(i).contains("合并")){
                                                    column2 = indexes.get(i);
                                                }
                                            }
                                            //实在没有就取第一个
                                            if(column2==-1){
                                                column2 = indexes.get(0);
                                            }
                                        }else if(matchText.size()==1){
                                            column2 = indexes.get(0);
                                        }
                                    }
                                }
                            }
                            for(int i=0;i<trs.size();i++){
                                Element tri = trs.get(i);
                                Elements tri_tds = tri.select("td");
                                if(column2==-1||column2==0){
                                    if(tri_tds.size()==3){
                                        column2=1;
                                    }else if(tri_tds.size()==4){
                                        column2=2;
                                    }
                                }
                                if(column2!=-1 && tri_tds.size()>column2 && tri_tds.size()>=3){
                                    String srcValue = tri_tds.get(column2).text();
                                    String srcName1 = tri_tds.get(0).text();
                                    Tu.Tuple2<Integer, String> tmpT = extractField(srcName1, srcValue, profitRules, unit);
                                    if(tmpT==null){
                                        String srcName2 = tri_tds.get(1).text();
                                        tmpT = extractField(srcName2, srcValue, profitRules, unit);
                                    }
                                    if(tmpT!=null){
                                        if(profitResultList.get(tmpT.getKey())==null){
                                            profitResultList.set(tmpT.getKey(),tmpT.getValue());
                                        }
                                    }
                                }

                            }

                        }else if("p".equals(child.tagName())||"h".equals(child.tagName())){
                            String curText = child.text();
                            if(curText.contains("现金流量表")){
                                condition = 4;
                                continue;
                            }
                        }
                    }else if(condition==4){
                        if(countP>=4){
                            break;
                        }
                        if("table".equals(child.tagName())){
                            Elements trs = child.select("tr");
                            //表格第一行
                            if(trs.size()>=1 && column3==-1){
                                Element tr0 = trs.get(0);
                                Elements tr0_tds = tr0.select("td");
                                List<Integer> indexes = new ArrayList<>();
                                List<String> matchText = new ArrayList<>();
                                for(int i=0;i<tr0_tds.size();i++){
                                    String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                    for(String yearStr:yearList){
                                        if(tr0_td_text.contains(yearStr)){
                                            matchText.add(tr0_td_text);
                                            indexes.add(i);
                                            break;
                                        }
                                    }
                                }
                                if(matchText.size()>1){
                                    //看谁有合并
                                    for(int i=0;i<matchText.size();i++){
                                        if(matchText.get(i).contains("合并")){
                                            column3 = indexes.get(i);
                                        }
                                    }
                                    //实在没有就取第一个
                                    if(column3==-1){
                                        column3 = indexes.get(0);
                                    }
                                }else if(matchText.size()==1){
                                    column3 = indexes.get(0);
                                }else if(matchText.size()==0){
                                    //没有匹配到的，说明可能在第二行
                                    if(trs.size()>=2 && column3==-1){
                                        tr0 = trs.get(1);
                                        tr0_tds = tr0.select("td");
                                        indexes = new ArrayList<>();
                                        matchText = new ArrayList<>();
                                        for(int i=0;i<tr0_tds.size();i++){
                                            String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                            for(String yearStr:yearList){
                                                if(tr0_td_text.contains(yearStr)){
                                                    matchText.add(tr0_td_text);
                                                    indexes.add(i);
                                                    break;
                                                }
                                            }

                                        }
                                        if(matchText.size()>1){
                                            //看谁有合并
                                            for(int i=0;i<matchText.size();i++){
                                                if(matchText.get(i).contains("合并")){
                                                    column3 = indexes.get(i);
                                                }
                                            }
                                            //实在没有就取第一个
                                            if(column3==-1){
                                                column3 = indexes.get(0);
                                            }
                                        }else if(matchText.size()==1){
                                            column3 = indexes.get(0);
                                        }
                                    }
                                }
                            }
                            for(int i=0;i<trs.size();i++){
                                Element tri = trs.get(i);
                                Elements tri_tds = tri.select("td");
                                if(column3==-1||column3==0){
                                    if(tri_tds.size()==3){
                                        column3=1;
                                    }else if(tri_tds.size()==4){
                                        column3=2;
                                    }
                                }
                                if(column3!=-1 && tri_tds.size()>column3 && tri_tds.size()>=3){
                                    String srcValue = tri_tds.get(column3).text();
                                    String srcName1 = tri_tds.get(0).text();
                                    Tu.Tuple2<Integer, String> tmpT = extractField(srcName1, srcValue, cashFlowRules, unit);
                                    if(tmpT==null){
                                        String srcName2 = tri_tds.get(1).text();
                                        tmpT = extractField(srcName2, srcValue, cashFlowRules, unit);
                                    }
                                    if(tmpT!=null){
                                        if(cashFlowResultList.get(tmpT.getKey())==null){
                                            cashFlowResultList.set(tmpT.getKey(),tmpT.getValue());
                                        }
                                    }
                                }

                            }
                            countFlag = true;

                        }
                        if(countFlag){
                            if(!"table".equals(child.tagName())){
                                countP++;
                            }
                        }
                    }
                }

            }

        }

        //还是不行，直接暴力表格搜索,看哪个都为null


        if(condition==0||verifyNull(balanceResultList)||verifyNull(profitResultList)||verifyNull(cashFlowResultList)) {
            condition = 0;
            column1 = -1;
            column2 = -1;
            column3 = -1;

            countFlag = false;
            countP = 0;

            for (Element element : es) {
                Elements children = element.children();
                for (int j = 0; j < children.size(); j++) {
                    Element child = children.get(j);
                    String text = child.text();
                    if (condition == 0 && child.tagName().equals("table")) {
                        Elements trs = child.select("tr");
                        boolean tmpFlag1 = false;
                        boolean tmpFlag2 = false;
                        boolean tmpFlag3 = false;
                        for(Element e:trs){
                            Elements tds = e.select("td");
                            if(tds.size()>=1){
                                String fieldName = tds.get(0).text();
                                if(fieldName.contains("流动资产")){
                                    tmpFlag1 = true;
                                }else if(fieldName.contains("货币资金")){
                                    tmpFlag2 = true;
                                }else if(fieldName.contains("应收账款")){
                                    tmpFlag3 = true;
                                }
                            }
                        }
                        if(tmpFlag1&&tmpFlag2&&tmpFlag3){
                            condition =1;
                            //往回退5行，获得一些基础信息
                            if(j-5>=0){
                                j = j-5;
                            }
                        }
                    }else if(condition==1){
                        if("p".equals(child.tagName())||"h".equals(child.tagName())){
                            //单位
                            String tmpText = child.text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");;
                            if(tmpText.contains("千元")){
                                unit = 1;
                            }else if(tmpText.contains("百万元")){
                                unit = 4;
                            }else if(tmpText.contains("十万元")){
                                unit = 3;
                            }else if(tmpText.contains("万元")){
                                unit = 2;
                            }
                        }else if("table".equals(child.tagName())){
                            Elements trs = child.select("tr");
                            //表格第一行
                            if(trs.size()>=1 && column1==-1){
                                Element tr0 = trs.get(0);
                                Elements tr0_tds = tr0.select("td");
                                List<Integer> indexes = new ArrayList<>();
                                List<String> matchText = new ArrayList<>();
                                for(int i=0;i<tr0_tds.size();i++){
                                    String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                    for(String yearStr:yearList){
                                        if(tr0_td_text.contains(yearStr)){
                                            matchText.add(tr0_td_text);
                                            indexes.add(i);
                                            break;
                                        }
                                    }
                                }
                                if(matchText.size()>1){
                                    //看谁有合并
                                    for(int i=0;i<matchText.size();i++){
                                        if(matchText.get(i).contains("合并")){
                                            column1 = indexes.get(i);
                                        }
                                    }
                                    //实在没有就取第一个
                                    if(column1==-1){
                                        column1 = indexes.get(0);
                                    }
                                }else if(matchText.size()==1){
                                    column1 = indexes.get(0);
                                }else if(matchText.size()==0){
                                    //没有匹配到的，说明可能在第二行
                                    if(trs.size()>=2 && column1==-1){
                                        tr0 = trs.get(1);
                                        tr0_tds = tr0.select("td");
                                        indexes = new ArrayList<>();
                                        matchText = new ArrayList<>();
                                        for(int i=0;i<tr0_tds.size();i++){
                                            String tr0_td_text = tr0_tds.get(i).text().replaceAll(" ","").replaceAll("\r","").replaceAll("\n","");
                                            for(String yearStr:yearList){
                                                if(tr0_td_text.contains(yearStr)){
                                                    matchText.add(tr0_td_text);
                                                    indexes.add(i);
                                                    break;
                                                }
                                            }

                                        }
                                        if(matchText.size()>1){
                                            //看谁有合并
                                            for(int i=0;i<matchText.size();i++){
                                                if(matchText.get(i).contains("合并")){
                                                    column1 = indexes.get(i);
                                                }
                                            }
                                            //实在没有就取第一个
                                            if(column1==-1){
                                                column1 = indexes.get(0);
                                            }
                                        }else if(matchText.size()==1){
                                            column1 = indexes.get(0);
                                        }
                                    }
                                }
                            }
                            for(int i=0;i<trs.size();i++){
                                Element tri = trs.get(i);
                                Elements tri_tds = tri.select("td");
                                if(column1==-1||column1==0){
                                    if(tri_tds.size()==3){
                                        column1=1;
                                    }else if(tri_tds.size()==4){
                                        column1=2;
                                    }
                                }
                                if(column1!=-1 && tri_tds.size()>column1 && tri_tds.size()>=3){
                                    String srcValue = tri_tds.get(column1).text();
                                    String srcName1 = tri_tds.get(0).text();
                                    if(verifyNull(balanceResultList)){
                                        Tu.Tuple2<Integer, String> tmpT = extractField(srcName1, srcValue, balanceRules, unit);
                                        if(tmpT==null){
                                            String srcName2 = tri_tds.get(1).text();
                                            tmpT = extractField(srcName2, srcValue, balanceRules, unit);
                                        }
                                        if(tmpT!=null){
                                            if(balanceResultList.get(tmpT.getKey())==null){
                                                balanceResultList.set(tmpT.getKey(),tmpT.getValue());
                                            }
                                        }
                                    }

                                    if(verifyNull(profitResultList)){
                                        Tu.Tuple2<Integer, String> tmpT2 = extractField(srcName1, srcValue, profitRules, unit);
                                        if(tmpT2==null){
                                            String srcName2 = tri_tds.get(1).text();
                                            tmpT2 = extractField(srcName2, srcValue, profitRules, unit);
                                        }
                                        if(tmpT2!=null){
                                            if(profitResultList.get(tmpT2.getKey())==null){
                                                profitResultList.set(tmpT2.getKey(),tmpT2.getValue());
                                            }
                                        }
                                    }

                                    if(verifyNull(cashFlowResultList)){
                                        Tu.Tuple2<Integer, String> tmpT3 = extractField(srcName1, srcValue, cashFlowRules, unit);
                                        if(tmpT3==null){
                                            String srcName2 = tri_tds.get(1).text();
                                            tmpT3 = extractField(srcName2, srcValue, cashFlowRules, unit);
                                        }
                                        if(tmpT3!=null){
                                            if(cashFlowResultList.get(tmpT3.getKey())==null){
                                                cashFlowResultList.set(tmpT3.getKey(),tmpT3.getValue());
                                            }
                                        }
                                    }


                                }

                            }


                        }

                    }
                }
            }


        }

        String pdfName = file.getName();

        String yearStr = pdfName.split("__")[4];
        String src = pdfName.split("__")[5];
        String code = pdfName.split("__")[2];
        String bondname = pdfName.split("__")[3];

        if(balanceResultList.get(0)!=null){
            if(!endFlag){
                balanceWriter.write(String.format("%s\001%s\001%s\001%s\001%s\n",yearStr, src, code, bondname,String.join("\001", balanceResultList)));
                profitWriter.write(String.format("%s\001%s\001%s\001%s\001%s\n",yearStr, src, code, bondname,String.join("\001", profitResultList)));
                cashflowWriter.write(String.format("%s\001%s\001%s\001%s\001%s\n",yearStr, src, code, bondname,String.join("\001", cashFlowResultList)));
            }else{
                balanceWriter.write(String.format("%s\001%s\001%s\001%s\001%s",yearStr, src, code, bondname,String.join("\001", balanceResultList)));
                profitWriter.write(String.format("%s\001%s\001%s\001%s\001%s",yearStr, src, code, bondname,String.join("\001", profitResultList)));
                cashflowWriter.write(String.format("%s\001%s\001%s\001%s\001%s",yearStr, src, code, bondname,String.join("\001", cashFlowResultList)));
            }

        }
    }

    public static boolean verifyNull(List<String> values){
        int count=3;
        int tmpCount=0;
        for(String str:values){
            if(str!=null){
                tmpCount++;
            }
        }
        return tmpCount <= count;

    }


    public static void get3Table(String[] args) throws IOException{
        String outputAllHtmlPath = "";
        if(args.length==2){
            File balanceFile = new File(args[1]+"\\balance.csv");
            File profitFile = new File(args[1]+"\\profit.csv");
            File cashflowFile = new File(args[1]+"\\cashflow.csv");

            try {
                balanceWriter = new FileWriter(balanceFile);
                profitWriter = new FileWriter(profitFile);
                cashflowWriter = new FileWriter(cashflowFile);
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
            outputAllHtmlPath = args[0];
        }else{
            outputAllHtmlPath = Path.outputAllHtmlPath;
        }



        File file = new File(outputAllHtmlPath);
        File[] files = file.listFiles();

        boolean endFlag = false;
        for(int i=0;i<files.length;i++){
            File f = files[i];
            System.out.println("正在处理:"+f.getName());
            if(i==files.length-1){
                handlerHtml(f,true);
            }else{
                handlerHtml(f,false);
            }
        }

        balanceWriter.close();
        profitWriter.close();
        cashflowWriter.close();
    }




}
