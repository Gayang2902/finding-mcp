package com.vulnshop.dto.response;

import lombok.*;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductListResponse {

    private List<ProductResponse> products;
    private long totalElements;
    private int totalPages;
    private int currentPage;
}
