package com.vulnshop.controller;

import com.vulnshop.dto.request.OrderCreateRequest;
import com.vulnshop.dto.request.OrderStatusUpdateRequest;
import com.vulnshop.dto.request.RefundRequest;
import com.vulnshop.dto.response.OrderResponse;
import com.vulnshop.dto.response.OrderSummaryResponse;
import com.vulnshop.dto.response.ShippingResponse;
import com.vulnshop.security.SecurityUtils;
import com.vulnshop.service.OrderService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping("/")
    public ResponseEntity<OrderResponse> createOrder(@Valid @RequestBody OrderCreateRequest request) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(orderService.createOrder(currentUserId, request));
    }

    @GetMapping("/")
    public ResponseEntity<List<OrderSummaryResponse>> getUserOrders() {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(orderService.getUserOrders(currentUserId));
    }

    // VULN: IDOR - no ownership check, any user can view any order by ID
    @GetMapping("/{id}")
    public ResponseEntity<OrderResponse> getOrderById(@PathVariable Long id) {
        return ResponseEntity.ok(orderService.getOrderById(id));
    }

    // VULN: IDOR - no ownership check, any user can view any order by number
    @GetMapping("/number/{orderNumber}")
    public ResponseEntity<OrderResponse> getOrderByNumber(@PathVariable String orderNumber) {
        return ResponseEntity.ok(orderService.getOrderByNumber(orderNumber));
    }

    // VULN: MFAC - no admin role check
    @PutMapping("/{id}/status")
    public ResponseEntity<OrderResponse> updateOrderStatus(@PathVariable Long id,
                                                           @Valid @RequestBody OrderStatusUpdateRequest request) {
        return ResponseEntity.ok(orderService.updateOrderStatus(id, request));
    }

    // VULN: IDOR - no ownership check
    @PutMapping("/{id}/cancel")
    public ResponseEntity<OrderResponse> cancelOrder(@PathVariable Long id) {
        return ResponseEntity.ok(orderService.cancelOrder(id));
    }

    // VULN: IDOR - no ownership check
    @GetMapping("/{id}/tracking")
    public ResponseEntity<OrderResponse> getOrderTracking(@PathVariable Long id) {
        return ResponseEntity.ok(orderService.getOrderTracking(id));
    }

    // VULN: IDOR - no ownership check
    @PostMapping("/{id}/refund")
    public ResponseEntity<OrderResponse> processRefund(@PathVariable Long id,
                                                       @RequestBody RefundRequest refundRequest) {
        return ResponseEntity.ok(orderService.processRefund(refundRequest));
    }

    // VULN: Missing access control - should be admin only
    @GetMapping("/all")
    public ResponseEntity<List<OrderResponse>> getAllOrders() {
        return ResponseEntity.ok(orderService.getAllOrders());
    }
}
