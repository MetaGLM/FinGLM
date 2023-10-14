package xfp.pdf.pojo;

import lombok.Data;

import java.util.List;


@Data
public class MarkPojo {
    private List<TitlePattern> titlePatterns;

    @Data
    public static class TitlePattern{
        private Integer order;
        private Float level;
        private String bold;
        private String pattern;
        private String firstPattern;
    }
}
