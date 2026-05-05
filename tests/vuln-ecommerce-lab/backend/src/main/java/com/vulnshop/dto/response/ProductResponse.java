package com.vulnshop.dto.response;

import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductResponse {

    private Long id;
    private String name;
    private String description;
    private BigDecimal price;
    private BigDecimal compareAtPrice;
    private String sku;
    private int stock;
    private String imageUrl;
    private String thumbnailUrl;
    private BigDecimal weight;
    private String dimensions;
    private boolean isActive;
    private double averageRating;
    private int reviewCount;
    private String categoryName;
    private Long categoryId;
    private String sellerName;
    private Long sellerId;
    private List<String> tags;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
