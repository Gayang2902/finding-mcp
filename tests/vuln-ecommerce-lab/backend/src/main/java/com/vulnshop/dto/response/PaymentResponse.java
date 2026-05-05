package com.vulnshop.dto.response;

import com.vulnshop.entity.PaymentMethod;
import com.vulnshop.entity.PaymentStatus;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PaymentResponse {

    private Long id;
    private Long orderId;
    private BigDecimal amount;
    private PaymentMethod method;
    private PaymentStatus status;
    private String transactionId;
    private String cardLastFour;
    private String cardBrand;
    private LocalDateTime createdAt;
    private LocalDateTime processedAt;
}
