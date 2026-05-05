package com.vulnshop.dto.request;

import jakarta.validation.constraints.Min;
import lombok.*;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CartUpdateRequest {

    @Min(value = 1, message = "Quantity must be at least 1")
    private int quantity;
}
