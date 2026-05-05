package com.vulnshop.service;

import com.vulnshop.dto.response.ShippingResponse;
import com.vulnshop.entity.Order;
import com.vulnshop.entity.ShippingEvent;
import com.vulnshop.entity.ShippingInfo;
import com.vulnshop.entity.ShippingStatus;
import com.vulnshop.exception.ResourceNotFoundException;
import com.vulnshop.repository.ShippingInfoRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional
public class ShippingService {

    private final ShippingInfoRepository shippingInfoRepository;

    public ShippingService(ShippingInfoRepository shippingInfoRepository) {
        this.shippingInfoRepository = shippingInfoRepository;
    }

    public ShippingResponse createShippingInfo(Order order) {
        String trackingNumber = "TRK-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();

        ShippingEvent initialEvent = ShippingEvent.builder()
                .timestamp(LocalDateTime.now())
                .location("Warehouse")
                .description("Order received and being prepared")
                .status(ShippingStatus.PREPARING)
                .build();

        ShippingInfo shippingInfo = ShippingInfo.builder()
                .order(order)
                .trackingNumber(trackingNumber)
                .status(ShippingStatus.PREPARING)
                .shippingMethod("Standard")
                .estimatedDelivery(LocalDateTime.now().plusDays(5))
                .events(new java.util.ArrayList<>(List.of(initialEvent)))
                .build();

        return mapToResponse(shippingInfoRepository.save(shippingInfo));
    }

    public ShippingResponse updateShippingStatus(Long shippingId, ShippingStatus status,
                                                  String location, String description) {
        ShippingInfo shippingInfo = shippingInfoRepository.findById(shippingId)
                .orElseThrow(() -> new ResourceNotFoundException("Shipping info not found: " + shippingId));

        shippingInfo.setStatus(status);

        if (status == ShippingStatus.DELIVERED) {
            shippingInfo.setActualDelivery(LocalDateTime.now());
        }

        ShippingEvent event = ShippingEvent.builder()
                .timestamp(LocalDateTime.now())
                .location(location)
                .description(description)
                .status(status)
                .build();
        shippingInfo.getEvents().add(event);

        return mapToResponse(shippingInfoRepository.save(shippingInfo));
    }

    // VULN: IDOR - returns shipping info without checking order ownership
    @Transactional(readOnly = true)
    public ShippingResponse getShippingByOrder(Long orderId) {
        ShippingInfo shippingInfo = shippingInfoRepository.findByOrderId(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Shipping info not found for order: " + orderId));
        return mapToResponse(shippingInfo);
    }

    @Transactional(readOnly = true)
    public ShippingResponse getShippingByTracking(String trackingNumber) {
        ShippingInfo shippingInfo = shippingInfoRepository.findByTrackingNumber(trackingNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Shipping info not found for tracking: " + trackingNumber));
        return mapToResponse(shippingInfo);
    }

    public ShippingResponse addShippingEvent(Long shippingId, ShippingEvent event) {
        ShippingInfo shippingInfo = shippingInfoRepository.findById(shippingId)
                .orElseThrow(() -> new ResourceNotFoundException("Shipping info not found: " + shippingId));
        shippingInfo.getEvents().add(event);
        return mapToResponse(shippingInfoRepository.save(shippingInfo));
    }

    public ShippingResponse mapToResponse(ShippingInfo info) {
        List<ShippingResponse.ShippingEventResponse> events = info.getEvents() == null ? List.of() :
                info.getEvents().stream()
                        .map(e -> ShippingResponse.ShippingEventResponse.builder()
                                .timestamp(e.getTimestamp())
                                .location(e.getLocation())
                                .description(e.getDescription())
                                .status(e.getStatus())
                                .build())
                        .collect(Collectors.toList());

        return ShippingResponse.builder()
                .id(info.getId())
                .carrier(info.getCarrier())
                .trackingNumber(info.getTrackingNumber())
                .estimatedDelivery(info.getEstimatedDelivery())
                .actualDelivery(info.getActualDelivery())
                .status(info.getStatus())
                .weight(info.getWeight())
                .shippingMethod(info.getShippingMethod())
                .shippingCost(info.getShippingCost())
                .events(events)
                .build();
    }
}
