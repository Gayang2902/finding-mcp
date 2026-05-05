package com.vulnshop.dto.request;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import lombok.*;
import java.math.BigDecimal;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RefundRequest {

    @NotNull(message = "Order ID is required")
    private Long orderId;

    @NotNull(message = "Reason is required")
    private String reason;

    @DecimalMin(value = "0.0", inclusive = false, message = "Refund amount must be positive")
    private BigDecimal amount;
}
