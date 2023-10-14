package xfp.pdf.thirdparty;

import org.apache.pdfbox.cos.COSBase;
import org.apache.pdfbox.cos.COSName;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.graphics.PDXObject;
import org.apache.pdfbox.pdmodel.graphics.form.PDFormXObject;
import org.apache.pdfbox.pdmodel.graphics.image.PDImageXObject;
import org.apache.pdfbox.util.Matrix;
import org.apache.pdfbox.contentstream.operator.DrawObject;
import org.apache.pdfbox.contentstream.operator.Operator;
import org.apache.pdfbox.contentstream.PDFStreamEngine;

import java.awt.geom.Rectangle2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

import org.apache.pdfbox.contentstream.operator.state.Concatenate;
import org.apache.pdfbox.contentstream.operator.state.Restore;
import org.apache.pdfbox.contentstream.operator.state.Save;
import org.apache.pdfbox.contentstream.operator.state.SetGraphicsStateParameters;
import org.apache.pdfbox.contentstream.operator.state.SetMatrix;
import xfp.pdf.pojo.Tu;

import javax.imageio.ImageIO;


public class GetImageEngine extends PDFStreamEngine
{
    public int imageNumber = 1;
    private String picSavePath;

    private final List<Tu.Tuple2<Integer,Rectangle2D.Float>> pics = new ArrayList<>();

    public List<Tu.Tuple2<Integer,Rectangle2D.Float>> getPics(){
        return pics;
    }
    public void clearList(){
        pics.clear();
    }

    public void setPicSavePath(String picSavePath) {
        this.picSavePath = picSavePath;
    }
    public String getPicSavePath(){
        return picSavePath;
    }


    public GetImageEngine(String picSavePath) throws IOException
    {
        this.picSavePath = picSavePath;
        // preparing PDFStreamEngine
        addOperator(new Concatenate());
        addOperator(new DrawObject());
        addOperator(new SetGraphicsStateParameters());
        addOperator(new Save());
        addOperator(new Restore());
        addOperator(new SetMatrix());
    }


    @Override
    protected void processOperator( Operator operator, List<COSBase> operands) throws IOException
    {
        String operation = operator.getName();
        if( "Do".equals(operation) )
        {
            COSName objectName = (COSName) operands.get( 0 );

            PDXObject xobject = getResources().getXObject( objectName );

            if( xobject instanceof PDImageXObject)
            {
                PDImageXObject image = (PDImageXObject)xobject;
                int imageWidth = image.getWidth();
                int imageHeight = image.getHeight();

                Matrix ctmNew = getGraphicsState().getCurrentTransformationMatrix();

                BufferedImage bImage = image.getImage();
                ImageIO.write(bImage,"PNG",new File(picSavePath + "/"+imageNumber+".png"));
                System.out.println("Image saved.");
                pics.add(new Tu.Tuple2<>(imageNumber,new Rectangle2D.Float(ctmNew.getTranslateX(), ctmNew.getTranslateY(), imageWidth, imageHeight)));


                imageNumber++;
            }
            else if(xobject instanceof PDFormXObject)
            {
                PDFormXObject form = (PDFormXObject)xobject;
                showForm(form);
            }
        }
        else
        {
            super.processOperator( operator, operands);
        }
    }

}