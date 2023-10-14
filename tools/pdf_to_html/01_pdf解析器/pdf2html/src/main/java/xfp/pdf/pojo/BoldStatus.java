package xfp.pdf.pojo;

import lombok.AllArgsConstructor;

@AllArgsConstructor

public enum BoldStatus {
    FullBord(2),
    PartBord(1),
    NoBord(0);
    int i;

    public int getStatus() {
        return i;
    }
}
