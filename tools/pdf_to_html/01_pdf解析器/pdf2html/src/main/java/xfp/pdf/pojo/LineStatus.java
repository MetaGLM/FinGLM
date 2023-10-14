package xfp.pdf.pojo;

import lombok.ToString;


@ToString
public enum LineStatus {
    Normal(0),
    ParaEnd(1),
    Footer(2),
    Header(3);

    LineStatus(int i) {

    }
}
