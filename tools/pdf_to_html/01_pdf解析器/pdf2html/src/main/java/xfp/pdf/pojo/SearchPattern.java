package xfp.pdf.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;


@Data
@AllArgsConstructor
@NoArgsConstructor
public class SearchPattern {
    String regexStr;
    BoldStatus boldStatus;
}
