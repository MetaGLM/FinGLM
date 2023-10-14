package xfp.pdf.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;


public class Tu {
    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class Tuple2<T,K> {
        private T key;
        private K value;
        @Override
        public String toString() {
            return key.toString();
        }
    }
    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class Tuple3<T,K,M> {
        private T value1;
        private K value2;
        private M value3;
    }
    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class Tuple4<T,K,M,P> {
        private T value1;
        private K value2;
        private M value3;
        private P value4;
    }
}
