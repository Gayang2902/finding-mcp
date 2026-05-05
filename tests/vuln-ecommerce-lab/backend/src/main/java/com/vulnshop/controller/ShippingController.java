package com.vulnshop.controller;

import com.vulnshop.dto.response.ShippingResponse;
import com.vulnshop.entity.ShippingStatus;
import com.vulnshop.service.ShippingService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/shipping")
public class ShippingController {

    private final ShippingService shippingService;

    public ShippingController(ShippingService shippingService) {
        this.shippingService = shippingService;
    }

    // VULN: IDOR - no ownership check, any user can view shipping info for any order
    @GetMapping("/order/{orderId}")
    public ResponseEntity<ShippingResponse> getShippingByOrder(@PathVariable Long orderId) {
        return ResponseEntity.ok(shippingService.getShippingByOrder(orderId));
    }

    @GetMapping("/track/{trackingNumber}")
    public ResponseEntity<ShippingResponse> getShippingByTracking(@PathVariable String trackingNumber) {
        return ResponseEntity.ok(shippingService.getShippingByTracking(trackingNumber));
    }

    // VULN: Missing access control - should be admin only
    @PutMapping("/{id}/status")
    public ResponseEntity<ShippingResponse> updateShippingStatus(@PathVariable Long id,
                                                                   @RequestParam ShippingStatus status,
                                                                   @RequestParam(required = false) String location,
                                                                   @RequestParam(required = false) String description) {
        return ResponseEntity.ok(shippingService.updateShippingStatus(id, status, location, description));
    }
}
