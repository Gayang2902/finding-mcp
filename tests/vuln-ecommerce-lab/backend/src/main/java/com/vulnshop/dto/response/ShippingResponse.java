package com.vulnshop.dto.response;

import com.vulnshop.entity.ShippingStatus;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ShippingResponse {

    private Long id;
    private String carrier;
    private String trackingNumber;
    private LocalDateTime estimatedDelivery;
    private LocalDateTime actualDelivery;
    private ShippingStatus status;
    private BigDecimal weight;
    private String shippingMethod;
    private BigDecimal shippingCost;
    private List<ShippingEventResponse> events;

    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ShippingEventResponse {
        private LocalDateTime timestamp;
        private String location;
        private String description;
        private ShippingStatus status;
    }
}
