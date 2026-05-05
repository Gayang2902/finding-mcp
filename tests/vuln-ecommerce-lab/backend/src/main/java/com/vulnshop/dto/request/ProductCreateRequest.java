package com.vulnshop.dto.request;

import jakarta.validation.constraints.*;
import lombok.*;
import java.math.BigDecimal;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductCreateRequest {

    @NotBlank(message = "Product name is required")
    private String name;

    private String description;

    @NotNull(message = "Price is required")
    @DecimalMin(value = "0.0", inclusive = false, message = "Price must be positive")
    private BigDecimal price;

    private BigDecimal compareAtPrice;

    private String sku;

    @Min(value = 0, message = "Stock cannot be negative")
    private int stock;

    private String imageUrl;

    private Long categoryId;

    private List<String> tags;

    private BigDecimal weight;

    private String dimensions;
}
