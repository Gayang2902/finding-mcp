package com.vulnshop.entity;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "shipping_info")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ShippingInfo {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "order_id", nullable = false, unique = true)
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private Order order;

    private String carrier;

    private String trackingNumber;

    private LocalDateTime estimatedDelivery;

    private LocalDateTime actualDelivery;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    @Builder.Default
    private ShippingStatus status = ShippingStatus.PREPARING;

    @Column(precision = 8, scale = 3)
    private BigDecimal weight;

    private String shippingMethod;

    @Column(precision = 10, scale = 2)
    private BigDecimal shippingCost;

    @ElementCollection
    @CollectionTable(name = "shipping_events", joinColumns = @JoinColumn(name = "shipping_info_id"))
    @Builder.Default
    @ToString.Exclude
    @EqualsAndHashCode.Exclude
    private List<ShippingEvent> events = new ArrayList<>();
}
