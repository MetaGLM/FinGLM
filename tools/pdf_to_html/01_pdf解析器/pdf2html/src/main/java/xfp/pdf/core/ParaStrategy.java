package xfp.pdf.core;

import org.apache.commons.collections4.CollectionUtils;
import org.apache.pdfbox.text.TextPosition;
import xfp.pdf.pojo.Language;
import xfp.pdf.pojo.Tu;
import xfp.pdf.tools.RenderInfo;
import xfp.pdf.tools.TextTool;


import java.util.ArrayList;
import java.util.List;

public class ParaStrategy {


    //策略1，比较前一行和当前行，当前行末尾是否有缩进
    public static boolean strategy1(List<Tu.Tuple2<TextPosition, RenderInfo>> preLine,
                                    List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,
                                    Float deltaLength){
        boolean flag1 = false;
        if(preLine.size()!=0){
            flag1 = UnTaggedAnalyser.compareEndTokenPos(preLine.get(preLine.size()-1).getKey(),curLine.get(curLine.size()-1).getKey(),deltaLength);
        }
        return flag1;
    }

    //策略2，比较当前和下一行，下一行的开头是否有缩进
    //该策略可能存在误判
    public static boolean strategy2(List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,
                                    List<Tu.Tuple2<TextPosition, RenderInfo>> postLine,
                                    Float deltaLength){
        boolean flag2 = false;
        if(postLine.size()==0){
            flag2 = true;
        }else{
            if(UnTaggedAnalyser.compareFirstTokenPos(curLine.get(0).getKey(), postLine.get(0).getKey(), deltaLength)){
                flag2 = true;
            }
        }
        return flag2;
    }

    //策略3，比较字体是否有区别
    public static boolean strategy3(List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,
                                    List<Tu.Tuple2<TextPosition, RenderInfo>> postLine){
        boolean flag3 = false;
        if(postLine.size()==0){
            flag3 = true;
        }else{
            if(UnTaggedAnalyser.compareTokenFont(curLine, postLine)){
                flag3 = true;
            }
        }
        return flag3;
    }

    //策略4,比较渲染方式是否有区别
    public static boolean strategy4(List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,
                                    List<Tu.Tuple2<TextPosition, RenderInfo>> postLine){
        boolean flag4 = false;
        if(postLine.size()==0){
            flag4 = true;
        }else{
            if(UnTaggedAnalyser.compareTokenRender(curLine.get(curLine.size()-1).getValue(),postLine.get(0).getValue())){
                flag4 = true;
            }
        }
        return flag4;
    }

    //策略5,通过preScan的信息来判断,当前行有缩进，下一行同样有缩进，上一行没有缩进
    public static boolean strategy5(List<Tu.Tuple2<TextPosition, RenderInfo>> preLine,
                                    List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,
                                    List<Tu.Tuple2<TextPosition, RenderInfo>> postLine,UnTaggedContext unTaggedContext,
                                    float deltaLength){
        boolean flag5 = false;
        float leftX = unTaggedContext.getLeftX();
        if(postLine.size()!=0){
            float x = curLine.get(0).getKey().getX();
            if(UnTaggedAnalyser.comparePos(leftX,x,deltaLength)){
                //当前行有缩进
                if(UnTaggedAnalyser.comparePos(leftX,postLine.get(0).getKey().getX(),deltaLength)){
                    //下一行同样有缩进
                    if(preLine.size()!=0){
                        float preX = preLine.get(0).getKey().getX();
                        if(!UnTaggedAnalyser.comparePos(leftX,preX,deltaLength)){
                            //当上一行的字体相同时，且上一行没有缩进
                            if(!UnTaggedAnalyser.compareTokenFont(preLine,curLine)){
                                flag5 = true;
                            }
                        }
                    }
                }
            }
        }
        return flag5;
    }

    //策略6，如果本行结尾小于preInfo的右边，为true
    public static boolean strategy6(List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,UnTaggedContext unTaggedContext,float deltaLength){
        boolean flag6 = false;
        float rightX = unTaggedContext.getRightX();
        float x = curLine.get(curLine.size() - 1).getKey().getX()+curLine.get(curLine.size() - 1).getKey().getWidth();
        if(UnTaggedAnalyser.comparePos(x,rightX,deltaLength)){
            flag6 = true;
        }
        return flag6;
    }


    /*
     xxxxxxxxx
     xxxxx      <- end
       xxxxxxx
     */
    public static boolean strategy11(List<Tu.Tuple2<TextPosition, RenderInfo>> preLine,List<Tu.Tuple2<TextPosition, RenderInfo>> curLine, List<Tu.Tuple2<TextPosition, RenderInfo>> postLine,
                                     UnTaggedContext unTaggedContext,float deltaLength){
        //本行开头没有缩进，下一行开头有缩进,上一行右侧无缩进
        boolean flag11 = false;
        Float leftX = unTaggedContext.getLeftX();
        Float rightX = unTaggedContext.getRightX();
        if(curLine.size()==0||postLine.size()==0){
            flag11 = true;
        }else{
            if(preLine.size()!=0){
                float curX = curLine.get(0).getKey().getX();
                float postX = postLine.get(0).getKey().getX();
                float preX = preLine.get(preLine.size() - 1).getKey().getX() + preLine.get(preLine.size() - 1).getKey().getWidth();
                //本行开头没有缩进，下一行开头有缩进,上一行右侧无缩进
                if(!UnTaggedAnalyser.comparePos(leftX,curX,deltaLength)&&UnTaggedAnalyser.comparePos(leftX,postX,deltaLength)
                    &&!UnTaggedAnalyser.comparePos(preX,rightX,deltaLength)){
                    flag11 = true;
                }
            }

        }
        return flag11;
    }


    //---------------英文策略-----------------------------------------------
    //策略7，如果本行较上一行的结尾有缩进，且较preInfo明显有缩进，为true
    public static boolean strategy7(List<Tu.Tuple2<TextPosition, RenderInfo>> preLine,
                                    List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,
                                    UnTaggedContext unTaggedContext,float deltaLength){
        boolean flag7 = false;
        if(!CollectionUtils.isEmpty(preLine)&&!CollectionUtils.isEmpty(curLine)){
            float preLinePos = preLine.get(preLine.size() - 1).getKey().getX() + preLine.get(preLine.size() - 1).getKey().getWidth();
            float postLinePos = curLine.get(curLine.size() - 1).getKey().getX() + curLine.get(curLine.size() - 1).getKey().getWidth();

            Float rightX = unTaggedContext.getRightX();
            if(postLinePos<preLinePos&&UnTaggedAnalyser.comparePos(postLinePos,rightX,deltaLength*3)){
                flag7 = true;
            }
        }
        return flag7;
    }

    //策略8，如果本行以句号结尾或者有足够的缩进，下一行的第一个英文字母是大写的，为true,或者下一行第一个英文字母是·,即unicode=61599，为true
    public static boolean strategy8(List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,List<Tu.Tuple2<TextPosition, RenderInfo>> postLine,
                                    UnTaggedContext unTaggedContext,float deltaLength){
        boolean flag8 = false;
        curLine = UnTaggedAnalyser.trimLine(curLine);
        postLine = UnTaggedAnalyser.trimLine(postLine);
        if(CollectionUtils.isEmpty(curLine)){
            return true;
        }
        if(CollectionUtils.isEmpty(postLine)){
            return true;
        }
        Float rightX = unTaggedContext.getRightX();
        //如果以一、这种的开头或者（1）这种的开头，无条件认为是段落
        String str = UnTaggedAnalyser.formLineString(postLine);
        if(str.matches("[一二三四五六七八九十]{1,3}[、.．][\\s\\S]*")){
            return true;
        }
        if(str.matches("[(（]?[1-9]{1,2}[)）][、.．]?[\\s\\S]*")){
            return true;
        }


        //本行以一些符号结尾或者结尾有缩进
        if(curLine.get(curLine.size() - 1).getKey().getUnicode().matches("[.;。]")
                ||UnTaggedAnalyser.comparePos(curLine.get(curLine.size() - 1).getKey().getX()+curLine.get(curLine.size() - 1).getKey().getWidth(),rightX,deltaLength*3)
            ){

            if(!TextTool.isContainChinese(postLine.get(0).getKey().getUnicode())&&!TextTool.isContainEnglish(postLine.get(0).getKey().getUnicode())
                    ){
                if(UnTaggedAnalyser.isTitle(postLine)){
                    return true;
                }
                if(!postLine.get(0).getKey().getUnicode().matches("[1-9]+")){
                    return true;
                }
            }


//            for(int i=0;i<postLine.size();i++){
//                if(i == 0){
////                    if(postLine.get(i).getKey().getUnicode().charAt(0) == 61599||postLine.get(i).getKey().getUnicode().charAt(0)==61623
////                        ||postLine.get(i).getKey().getUnicode().charAt(0)==111){
////                        return true;
////                    }
//                    //以特殊字符开头的
//                    if(!TextTool.isContainChinese(postLine.get(i).getKey().getUnicode())&&!TextTool.isContainEnglish(postLine.get(i).getKey().getUnicode())
//                        &&!postLine.get(i).getKey().getUnicode().matches("[1-9]+")){
//                        return true;
//                    }
//                }
//                Tu.Tuple2<TextPosition, RenderInfo> p = postLine.get(i);
//                String unicode = p.getKey().getUnicode();
//                if(TextTool.isContainEnglish(unicode)){
//                    if(unicode.toUpperCase().equals(unicode)){
//                        flag8 = true;
//                    }else{
//                        flag8 = false;
//                    }
//                    break;
//                }
//            }
        }
        return flag8;
    }

    //策略9，如果下一行较本行的距离和本行较上一行的距离明显大，为true
    //而且同时需要curLine结尾为特殊符号，如。才能为true
    public static boolean strategy9(List<Tu.Tuple2<TextPosition, RenderInfo>> preLine,
                                    List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,
                                    List<Tu.Tuple2<TextPosition, RenderInfo>> postLine){
        List<String> stopChars = new ArrayList<>();
        stopChars.add(",");
        stopChars.add("，");
        stopChars.add("、");

        boolean flag9 = false;
        if(!CollectionUtils.isEmpty(preLine)&&!CollectionUtils.isEmpty(curLine)&&!CollectionUtils.isEmpty(postLine)){
//            System.out.println(preLine.get(0).getKey().getY());
//            System.out.println(curLine.get(0).getKey().getY());
//            System.out.println(postLine.get(0).getKey().getY());
            float preSpace = curLine.get(0).getKey().getY() - preLine.get(0).getKey().getY() - curLine.get(0).getKey().getHeight();
            float postSpace = postLine.get(0).getKey().getY() - curLine.get(0).getKey().getY() - postLine.get(0).getKey().getHeight();
//            System.out.println("preSpace:"+preSpace);
//            System.out.println("postSpace:"+postSpace);

            if(postSpace>1.2*preSpace){
                String unicode = curLine.get(curLine.size() - 1).getKey().getUnicode();

                if(!TextTool.isContainEnglish(unicode)&&!TextTool.isContainChinese(unicode)
                    &&!stopChars.contains(unicode)){
                    flag9 = true;
                }
            }
        }
        return flag9;
    }

    //策略10，无条件策略，当本行右边的缩进已经达到了六倍的deltaLength，无条件成为段尾
    public static boolean strategy10(List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,UnTaggedContext unTaggedContext,float deltaLength){
        curLine = UnTaggedAnalyser.trimLine(curLine);
        if(CollectionUtils.isEmpty(curLine)){
            return true;
        }
        Float rightX = unTaggedContext.getRightX();
        float curRightX = curLine.get(curLine.size() - 1).getKey().getX() + curLine.get(curLine.size() - 1).getKey().getWidth();
        if(UnTaggedAnalyser.comparePos(curRightX,rightX,deltaLength*6)){
            return true;
        }
        return false;
    }


    //页面第一行判断策略1
    public static boolean firstLineStrategy1(List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,
                                             List<Tu.Tuple2<TextPosition, RenderInfo>> postLine,Float deltaLength){
        //如果第一行和第二行的结束位置相同，且结尾没有句号，分号，那么除非字体不相同，均不能认为是不同的段落。
        curLine = UnTaggedAnalyser.trimLine(curLine);
        postLine = UnTaggedAnalyser.trimLine(postLine);
        if(CollectionUtils.isEmpty(curLine)||CollectionUtils.isEmpty(postLine)){
            return true;
        }
        float curLineRightX = curLine.get(curLine.size() - 1).getKey().getX() + curLine.get(curLine.size() - 1).getKey().getWidth();
        float postLineRightX = postLine.get(postLine.size() - 1).getKey().getX() + postLine.get(postLine.size() - 1).getKey().getWidth();
        if(!UnTaggedAnalyser.comparePos(curLineRightX,postLineRightX,deltaLength)&&!UnTaggedAnalyser.comparePos(postLineRightX,curLineRightX,deltaLength)){
            //结束位置相同
            boolean b = curLine.get(curLine.size() - 1).getKey().getUnicode().matches("[.;。；]");
            if(b){
                return true;
            }
            boolean b1 = UnTaggedAnalyser.compareTokenFont(curLine, postLine);
            if(b1){
                return true;
            }
        }else{
            //结束位置不同
            //如果第二行较第一行有缩进，那么再判断一下字体样式，如果字体一致的，仍认为并非是段尾
            if(UnTaggedAnalyser.comparePos(postLineRightX,curLineRightX,deltaLength)){
                return UnTaggedAnalyser.compareTokenFont(curLine, postLine);
            }

            return true;
        }
        return false;
    }

    //页面最后一行判断策略2
    public static boolean lastLineStrategy1( List<Tu.Tuple2<TextPosition, RenderInfo>> curLine,UnTaggedContext unTaggedContext,float deltaLength){
        float rightX = unTaggedContext.getRightX();
        if(UnTaggedAnalyser.comparePos(curLine.get(curLine.size()-1).getKey().getX(),rightX,deltaLength)){
           return true;
        }
        return false;
    }

    //文本内容判断策略1
    public static boolean referParaEndByContent1(List<Tu.Tuple2<TextPosition, RenderInfo>> line,UnTaggedContext unTaggedContext){
        line = UnTaggedAnalyser.trimLine(line);
        if(CollectionUtils.isEmpty(line)||line.size()==1){
            return false;
        }
        Tu.Tuple2<TextPosition, RenderInfo> first = line.get(0);
        Tu.Tuple2<TextPosition, RenderInfo> last = line.get(line.size() - 1);
        if(unTaggedContext.getLanguage()== Language.CHINESE){
//            if(first.getKey().getUnicode().matches("[0-9]")||first.getKey().getUnicode().matches("[(（·]")){
//                if(last.getKey().getUnicode().matches("[.;。；]")){
//                    return true;
//                }
//            }

            if(!TextTool.isContainChinese(first.getKey().getUnicode())&&!TextTool.isContainEnglish(first.getKey().getUnicode())){
                //如果开头符合目录的特征的话也行
                if(UnTaggedAnalyser.isTitle(line)){
                    if(last.getKey().getUnicode().matches("[.;。；]")){
                        return true;
                    }
                }
                if(!first.getKey().getUnicode().matches("[1-9]+")){
                    if(last.getKey().getUnicode().matches("[.;。；]")){
                        return true;
                    }
                }

            }
//            if(first.getKey().getUnicode().matches("[(（·]")){
//                if(last.getKey().getUnicode().matches("[.;。；]")){
//                    return true;
//                }
//            }
        }else if(unTaggedContext.getLanguage()==Language.ENGLISH){
            if(last.getKey().getUnicode().matches("[.;。；]")){
                return true;
            }
        }

        return false;
    }




}
