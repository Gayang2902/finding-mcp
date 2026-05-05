package com.vulnshop.entity;

import jakarta.persistence.Embeddable;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import lombok.*;
import java.time.LocalDateTime;

@Embeddable
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ShippingEvent {

    private LocalDateTime timestamp;

    private String location;

    private String description;

    @Enumerated(EnumType.STRING)
    private ShippingStatus status;
}
