package com.vulnshop.dto.request;

import lombok.*;
import java.math.BigDecimal;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductSearchRequest {

    private String query;

    private Long categoryId;

    private BigDecimal minPrice;

    private BigDecimal maxPrice;

    @Builder.Default
    private String sortBy = "createdAt";

    @Builder.Default
    private String sortDirection = "DESC";

    @Builder.Default
    private int page = 0;

    @Builder.Default
    private int size = 20;
}
