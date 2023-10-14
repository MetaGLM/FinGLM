package xfp.pdf.thirdparty;

import org.apache.pdfbox.pdmodel.font.PDFont;
import org.apache.pdfbox.pdmodel.graphics.color.PDColor;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotation;
import org.apache.pdfbox.rendering.PageDrawer;
import org.apache.pdfbox.rendering.PageDrawerParameters;
import org.apache.pdfbox.util.Matrix;
import org.apache.pdfbox.util.Vector;

import java.awt.*;
import java.awt.geom.AffineTransform;
import java.awt.geom.GeneralPath;
import java.awt.geom.PathIterator;
import java.awt.geom.Rectangle2D;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;


public class CustomPageDrawer extends PageDrawer {

    private List<Shape> tableLines = new ArrayList<>();

    private List<Shape> strokeLines = new ArrayList<>();

    private List<Shape> fillLines = new ArrayList<>();

    private List<Shape> fillAndStrokeLine = new ArrayList<>();

    public List<Shape> getFillAndStrokeLine() {
        return fillAndStrokeLine;
    }

    public List<Shape> getStrokeLines() {
        return strokeLines;
    }

    public List<Shape> getFillLines() {
        return fillLines;
    }

    public List<Shape> getTableLines() {
        return tableLines;
    }

    public void setTableLines(List<Shape> tableLines) {
        this.tableLines = tableLines;
    }

    CustomPageDrawer(PageDrawerParameters parameters) throws IOException
    {
        super(parameters);
    }


    @Override
    protected Paint getPaint(PDColor color) throws IOException
    {
        try{
            if (getGraphicsState().getNonStrokingColor() == color)
            {
                if (color.toRGB() == (Color.RED.getRGB() & 0x00FFFFFF))
                {
                    return Color.BLUE;
                }
            }
        }catch (Exception e){
            return super.getPaint(color);
        }
        return super.getPaint(color);
    }


    @Override
    protected void showGlyph(Matrix textRenderingMatrix, PDFont font, int code, String unicode,
                             Vector displacement) throws IOException
    {
        super.showGlyph(textRenderingMatrix, font, code, unicode, displacement);

        Shape bbox = new Rectangle2D.Float(0, 0, font.getWidth(code) / 1000, 1);
        AffineTransform at = textRenderingMatrix.createAffineTransform();
        bbox = at.createTransformedShape(bbox);


        Graphics2D graphics = getGraphics();
        Color color = graphics.getColor();
        Stroke stroke = graphics.getStroke();
        Shape clip = graphics.getClip();


        graphics.setClip(graphics.getDeviceConfiguration().getBounds());
        graphics.setColor(Color.BLACK);
        graphics.setStroke(new BasicStroke(.5f));
        graphics.draw(bbox);

        graphics.setStroke(stroke);
        graphics.setColor(color);
        graphics.setClip(clip);
    }


    @Override
    public void fillPath(int windingRule) throws IOException
    {

        Shape bbox = getLinePath().getBounds2D();

        if(bbox.getBounds2D().getWidth()>1.0f||bbox.getBounds2D().getHeight()>1.0f){
            fillLines.add(bbox);
        }


        super.fillPath(windingRule);

        Graphics2D graphics = getGraphics();
        Color color = graphics.getColor();
        Stroke stroke = graphics.getStroke();
        Shape clip = graphics.getClip();

        graphics.setClip(graphics.getDeviceConfiguration().getBounds());
        graphics.setColor(Color.RED);
        graphics.setStroke(new BasicStroke(.5f));
        if(bbox.getBounds2D().getWidth()>1.0f||bbox.getBounds2D().getHeight()>1.0f){
            graphics.draw(bbox);
        }

        graphics.setStroke(stroke);
        graphics.setColor(color);
        graphics.setClip(clip);

        getLinePath().reset();
    }

    @Override
    public void strokePath() throws IOException
    {

        Shape bbox = getLinePath().getBounds2D();

        if(bbox.getBounds2D().getWidth()>1.0f||bbox.getBounds2D().getHeight()>1.0f){
            strokeLines.add(bbox);
        }

        Graphics2D graphics = getGraphics();
        Color color = graphics.getColor();
        Stroke stroke = graphics.getStroke();
        Shape clip = graphics.getClip();


        graphics.setClip(graphics.getDeviceConfiguration().getBounds());
        graphics.setColor(Color.RED);
        graphics.setStroke(new BasicStroke(.5f));
        graphics.draw(bbox);

        graphics.setStroke(stroke);
        graphics.setColor(color);
        graphics.setClip(clip);

        getLinePath().reset();
    }

    @Override
    public void closePath() {
        Shape bbox = getLinePath().getBounds2D();

        if(bbox.getBounds2D().getWidth()>1.0f||bbox.getBounds2D().getHeight()>1.0f){
            fillAndStrokeLine.add(bbox);
        }

        Graphics2D graphics = getGraphics();
        Color color = graphics.getColor();
        Stroke stroke = graphics.getStroke();
        Shape clip = graphics.getClip();


        graphics.setClip(graphics.getDeviceConfiguration().getBounds());
        graphics.setColor(Color.RED);
        graphics.setStroke(new BasicStroke(.5f));
        graphics.draw(bbox);

        graphics.setStroke(stroke);
        graphics.setColor(color);
        graphics.setClip(clip);

        getLinePath().reset();
    }


    @Override
    public void showAnnotation(PDAnnotation annotation) throws IOException
    {
        // save
        saveGraphicsState();
        // 35% alpha
        getGraphicsState().setNonStrokeAlphaConstants(0.35);
        super.showAnnotation(annotation);
        // restore
        restoreGraphicsState();
    }

    int countlines = 0;

    void printPath()
    {

        GeneralPath path = getLinePath();
        PathIterator pathIterator = path.getPathIterator(null);

        double x = 0, y = 0;
        double coords[] = new double[6];
        while (!pathIterator.isDone()) {
            countlines ++;
            switch (pathIterator.currentSegment(coords)) {
                case PathIterator.SEG_MOVETO:
                    x = coords[0];
                    y = coords[1];
                    break;
                case PathIterator.SEG_LINETO:
                    double width = getEffectiveWidth(coords[0] - x, coords[1] - y);
                    x = coords[0];
                    y = coords[1];
                    break;
                case PathIterator.SEG_QUADTO:
                    x = coords[2];
                    y = coords[3];
                    break;
                case PathIterator.SEG_CUBICTO:
                    x = coords[4];
                    y = coords[5];
                    break;
                case PathIterator.SEG_CLOSE:
                    System.out.println("Close path");
            }
            pathIterator.next();
        }
    }

    double getEffectiveWidth(double dirX, double dirY)
    {
        if (dirX == 0 && dirY == 0)
            return 0;
        Matrix ctm = getGraphicsState().getCurrentTransformationMatrix();
        double widthX = dirY;
        double widthY = -dirX;
        double widthXTransformed = widthX * ctm.getValue(0, 0) + widthY * ctm.getValue(1, 0);
        double widthYTransformed = widthX * ctm.getValue(0, 1) + widthY * ctm.getValue(1, 1);
        double factor = Math.sqrt((widthXTransformed*widthXTransformed + widthYTransformed*widthYTransformed) / (widthX*widthX + widthY*widthY));
        return getGraphicsState().getLineWidth() * factor;
    }
}
