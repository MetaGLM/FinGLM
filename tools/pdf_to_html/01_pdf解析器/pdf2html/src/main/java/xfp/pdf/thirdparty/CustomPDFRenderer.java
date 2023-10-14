package xfp.pdf.thirdparty;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;
import org.apache.pdfbox.cos.COSName;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.pdmodel.PDResources;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.graphics.blend.BlendMode;
import org.apache.pdfbox.pdmodel.graphics.optionalcontent.PDOptionalContentGroup;
import org.apache.pdfbox.pdmodel.graphics.optionalcontent.PDOptionalContentProperties;
import org.apache.pdfbox.pdmodel.graphics.state.PDExtendedGraphicsState;
import org.apache.pdfbox.pdmodel.interactive.annotation.AnnotationFilter;
import org.apache.pdfbox.pdmodel.interactive.annotation.PDAnnotation;
import org.apache.pdfbox.rendering.*;
//
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.util.StringTokenizer;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class CustomPDFRenderer extends PDFRenderer{

    private static final Log LOG = LogFactory.getLog(PDFRenderer.class);
    private static Class<?> pageDrawerParametersC;
    static {
        try {
            pageDrawerParametersC = Class.forName("org.apache.pdfbox.rendering.PageDrawerParameters");
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
    }

    protected final PDDocument document;


    private AnnotationFilter annotationFilter = new AnnotationFilter()
    {
        @Override
        public boolean accept(PDAnnotation annotation)
        {
            return true;
        }
    };

    private boolean subsamplingAllowed = false;

    private RenderDestination defaultDestination;

    private RenderingHints renderingHints = null;

    private BufferedImage pageImage;

    private static boolean kcmsLogged = false;

    private float imageDownscalingOptimizationThreshold = 0.5f;

    private xfp.pdf.thirdparty.CustomPageDrawer pageDrawer;


    public CustomPDFRenderer(PDDocument document)
    {
        super(document);
        this.document = document;

        if (!kcmsLogged)
        {
            suggestKCMS();
            kcmsLogged = true;
        }
    }

    @Override
    protected PageDrawer createPageDrawer(PageDrawerParameters parameters) throws IOException
    {
        pageDrawer = new  xfp.pdf.thirdparty.CustomPageDrawer(parameters);
        return pageDrawer;
    }

    public xfp.pdf.thirdparty.CustomPageDrawer getDrawer(){
        return pageDrawer;
    }


    public AnnotationFilter getAnnotationsFilter()
    {
        return annotationFilter;
    }


    public void setAnnotationsFilter(AnnotationFilter annotationsFilter)
    {
        this.annotationFilter = annotationsFilter;
    }


    public boolean isSubsamplingAllowed()
    {
        return subsamplingAllowed;
    }


    public void setSubsamplingAllowed(boolean subsamplingAllowed)
    {
        this.subsamplingAllowed = subsamplingAllowed;
    }


    public RenderDestination getDefaultDestination()
    {
        return defaultDestination;
    }


    public void setDefaultDestination(RenderDestination defaultDestination)
    {
        this.defaultDestination = defaultDestination;
    }


    public RenderingHints getRenderingHints()
    {
        return renderingHints;
    }


    public void setRenderingHints(RenderingHints renderingHints)
    {
        this.renderingHints = renderingHints;
    }


    public float getImageDownscalingOptimizationThreshold()
    {
        return imageDownscalingOptimizationThreshold;
    }


    public void setImageDownscalingOptimizationThreshold(float imageDownscalingOptimizationThreshold)
    {
        this.imageDownscalingOptimizationThreshold = imageDownscalingOptimizationThreshold;
    }


    public BufferedImage renderImage(int pageIndex) throws IOException
    {
        return renderImage(pageIndex, 1);
    }


    public BufferedImage renderImage(int pageIndex, float scale) throws IOException
    {
        return renderImage(pageIndex, scale, ImageType.RGB);
    }


    public BufferedImage renderImageWithDPI(int pageIndex, float dpi) throws IOException
    {
        return renderImage(pageIndex, dpi / 72f, ImageType.RGB);
    }


    public BufferedImage renderImageWithDPI(int pageIndex, float dpi, ImageType imageType)
            throws IOException
    {
        return renderImage(pageIndex, dpi / 72f, imageType);
    }


    public BufferedImage renderImage(int pageIndex, float scale, ImageType imageType)
            throws IOException
    {
        return renderImage(pageIndex, scale, imageType,
                defaultDestination == null ? RenderDestination.EXPORT : defaultDestination);
    }


    public BufferedImage renderImage(int pageIndex, float scale, ImageType imageType, RenderDestination destination)
            throws IOException
    {
        PDPage page = document.getPage(pageIndex);

        PDRectangle cropbBox = page.getCropBox();
        float widthPt = cropbBox.getWidth();
        float heightPt = cropbBox.getHeight();

        // PDFBOX-4306 avoid single blank pixel line on the right or on the bottom
        int widthPx = (int) Math.max(Math.floor(widthPt * scale), 1);
        int heightPx = (int) Math.max(Math.floor(heightPt * scale), 1);

        // PDFBOX-4518 the maximum size (w*h) of a buffered image is limited to Integer.MAX_VALUE
        if ((long) widthPx * (long) heightPx > Integer.MAX_VALUE)
        {
            throw new IOException("Maximum size of image exceeded (w * h * scale ^ 2) = "//
                    + widthPt + " * " + heightPt + " * " + scale + " ^ 2 > " + Integer.MAX_VALUE);
        }

        int rotationAngle = page.getRotation();

        int bimType = 1;

        if (imageType != ImageType.ARGB && hasBlendMode(page))
        {
            bimType = BufferedImage.TYPE_INT_ARGB;
        }

        BufferedImage image;
        if (rotationAngle == 90 || rotationAngle == 270)
        {
            image = new BufferedImage(heightPx, widthPx, bimType);
        }
        else
        {
            image = new BufferedImage(widthPx, heightPx, bimType);
        }

        pageImage = image;

        Graphics2D g = image.createGraphics();
        if (image.getType() == BufferedImage.TYPE_INT_ARGB)
        {
            g.setBackground(new Color(0, 0, 0, 0));
        }
        else
        {
            g.setBackground(Color.WHITE);
        }
        g.clearRect(0, 0, image.getWidth(), image.getHeight());

        transform(g, page, scale, scale);

        RenderingHints actualRenderingHints =
                renderingHints == null ? createDefaultRenderingHints(g) : renderingHints;

        Class[] cls = {PDFRenderer.class, PDPage.class, boolean.class,
        RenderDestination.class, RenderingHints.class, float.class};


        Constructor<?> constructor = null;
        Object o = null;
        try {
            constructor = pageDrawerParametersC.getDeclaredConstructor(cls);
            constructor.setAccessible(true);
            o = constructor.newInstance(this,page,subsamplingAllowed,destination
                    ,actualRenderingHints,imageDownscalingOptimizationThreshold);
        } catch (InstantiationException | IllegalAccessException | InvocationTargetException | NoSuchMethodException e) {
            e.printStackTrace();
        }

        PageDrawerParameters parameters = (PageDrawerParameters) o;

        PageDrawer drawer = createPageDrawer(parameters);

        drawer.drawPage(g, page.getCropBox());

        g.dispose();

        if (image.getType() != 1)
        {
            BufferedImage newImage =
                    new BufferedImage(image.getWidth(), image.getHeight(), 1);
            Graphics2D dstGraphics = newImage.createGraphics();
            dstGraphics.setBackground(Color.WHITE);
            dstGraphics.clearRect(0, 0, image.getWidth(), image.getHeight());
            dstGraphics.drawImage(image, 0, 0, null);
            dstGraphics.dispose();
            image = newImage;
        }

        return image;
    }


    public void renderPageToGraphics(int pageIndex, Graphics2D graphics) throws IOException
    {
        renderPageToGraphics(pageIndex, graphics, 1);
    }


    public void renderPageToGraphics(int pageIndex, Graphics2D graphics, float scale)
            throws IOException
    {
        renderPageToGraphics(pageIndex, graphics, scale, scale);
    }


    public void renderPageToGraphics(int pageIndex, Graphics2D graphics, float scaleX, float scaleY)
            throws IOException
    {
        renderPageToGraphics(pageIndex, graphics, scaleX, scaleY,
                defaultDestination == null ? RenderDestination.VIEW : defaultDestination);
    }


    public void renderPageToGraphics(int pageIndex, Graphics2D graphics, float scaleX, float scaleY, RenderDestination destination)
            throws IOException
    {
        PDPage page = document.getPage(pageIndex);
        // TODO need width/height calculations? should these be in PageDrawer?

        transform(graphics, page, scaleX, scaleY);

        PDRectangle cropBox = page.getCropBox();
        graphics.clearRect(0, 0, (int) cropBox.getWidth(), (int) cropBox.getHeight());

        // the end-user may provide a custom PageDrawer
        RenderingHints actualRenderingHints =
                renderingHints == null ? createDefaultRenderingHints(graphics) : renderingHints;

        Class[] cls = {PDFRenderer.class, PDPage.class, boolean.class,
                RenderDestination.class, RenderingHints.class, float.class};

        Constructor<?> constructor = null;
        Object o = null;
        try {
            constructor = pageDrawerParametersC.getDeclaredConstructor(cls);
            constructor.setAccessible(true);
            o = constructor.newInstance(this,page,subsamplingAllowed,destination
                    ,actualRenderingHints,imageDownscalingOptimizationThreshold);
        } catch (InstantiationException | IllegalAccessException | InvocationTargetException | NoSuchMethodException e) {
            e.printStackTrace();
        }

        PageDrawerParameters parameters = (PageDrawerParameters)o;

        PageDrawer drawer = createPageDrawer(parameters);
        drawer.drawPage(graphics, cropBox);
    }


    public boolean isGroupEnabled(PDOptionalContentGroup group)
    {
        PDOptionalContentProperties ocProperties = document.getDocumentCatalog().getOCProperties();
        return ocProperties == null || ocProperties.isGroupEnabled(group);
    }

    // scale rotate translate
    private void transform(Graphics2D graphics, PDPage page, float scaleX, float scaleY)
    {
        graphics.scale(scaleX, scaleY);

        int rotationAngle = page.getRotation();
        PDRectangle cropBox = page.getCropBox();

        if (rotationAngle != 0)
        {
            float translateX = 0;
            float translateY = 0;
            switch (rotationAngle)
            {
                case 90:
                    translateX = cropBox.getHeight();
                    break;
                case 270:
                    translateY = cropBox.getWidth();
                    break;
                case 180:
                    translateX = cropBox.getWidth();
                    translateY = cropBox.getHeight();
                    break;
                default:
                    break;
            }
            graphics.translate(translateX, translateY);
            graphics.rotate(Math.toRadians(rotationAngle));
        }
    }

    private boolean isBitonal(Graphics2D graphics)
    {
        GraphicsConfiguration deviceConfiguration = graphics.getDeviceConfiguration();
        if (deviceConfiguration == null)
        {
            return false;
        }
        GraphicsDevice device = deviceConfiguration.getDevice();
        if (device == null)
        {
            return false;
        }
        DisplayMode displayMode = device.getDisplayMode();
        if (displayMode == null)
        {
            return false;
        }
        return displayMode.getBitDepth() == 1;
    }

    private RenderingHints createDefaultRenderingHints(Graphics2D graphics)
    {
        RenderingHints r = new RenderingHints(null);
        r.put(RenderingHints.KEY_INTERPOLATION, isBitonal(graphics) ?
                RenderingHints.VALUE_INTERPOLATION_NEAREST_NEIGHBOR :
                RenderingHints.VALUE_INTERPOLATION_BICUBIC);
        r.put(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
        r.put(RenderingHints.KEY_ANTIALIASING, isBitonal(graphics) ?
                RenderingHints.VALUE_ANTIALIAS_OFF :
                RenderingHints.VALUE_ANTIALIAS_ON);
        return r;
    }


    private boolean hasBlendMode(PDPage page)
    {
        // check the current resources for blend modes
        PDResources resources = page.getResources();
        if (resources == null)
        {
            return false;
        }
        for (COSName name : resources.getExtGStateNames())
        {
            PDExtendedGraphicsState extGState = resources.getExtGState(name);
            if (extGState == null)
            {
                continue;
            }
            BlendMode blendMode = extGState.getBlendMode();
            if (blendMode != BlendMode.NORMAL)
            {
                return true;
            }
        }
        return false;
    }


    BufferedImage getPageImage()
    {
        return pageImage;
    }

    private static void suggestKCMS()
    {
        String cmmProperty = System.getProperty("sun.java2d.cmm");
        if (isMinJdk8() && !"sun.java2d.cmm.kcms.KcmsServiceProvider".equals(cmmProperty))
        {
            try
            {
                // Make sure that class exists
                Class.forName("sun.java2d.cmm.kcms.KcmsServiceProvider");

                String version = System.getProperty("java.version");
                if (version == null ||
                        isGoodVersion(version, "1.8.0_(\\d+)", 191) ||
                        isGoodVersion(version, "9.0.(\\d+)", 4))
                {
                    return;
                }
                LOG.info("Your current java version is: " + version);
                LOG.info("To get higher rendering speed on old java 1.8 or 9 versions,");
                LOG.info("  update to the latest 1.8 or 9 version (>= 1.8.0_191 or >= 9.0.4),");
                LOG.info("  or");
                LOG.info("  use the option -Dsun.java2d.cmm=sun.java2d.cmm.kcms.KcmsServiceProvider");
                LOG.info("  or call System.setProperty(\"sun.java2d.cmm\", \"sun.java2d.cmm.kcms.KcmsServiceProvider\")");
            }
            catch (ClassNotFoundException e)
            {
                // KCMS not available
            }
        }
    }

    private static boolean isGoodVersion(String version, String regex, int min)
    {
        Matcher matcher = Pattern.compile(regex).matcher(version);
        if (matcher.matches() && matcher.groupCount() >= 1)
        {
            try
            {
                int v = Integer.parseInt(matcher.group(1));
                if (v >= min)
                {
                    return true;
                }
            }
            catch (NumberFormatException ex)
            {
                return true;
            }
        }
        return false;
    }

    private static boolean isMinJdk8()
    {
        String version = System.getProperty("java.specification.version");
        final StringTokenizer st = new StringTokenizer(version, ".");
        try
        {
            int major = Integer.parseInt(st.nextToken());
            int minor = 0;
            if (st.hasMoreTokens())
            {
                minor = Integer.parseInt(st.nextToken());
            }
            return major > 1 || (major == 1 && minor >= 8);
        }
        catch (NumberFormatException nfe)
        {
            return true;
        }
    }
}
