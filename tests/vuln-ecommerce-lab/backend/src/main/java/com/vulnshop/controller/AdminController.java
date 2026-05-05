package com.vulnshop.controller;

import com.vulnshop.dto.request.OrderStatusUpdateRequest;
import com.vulnshop.dto.request.ProductSearchRequest;
import com.vulnshop.dto.response.*;
import com.vulnshop.entity.AuditLog;
import com.vulnshop.entity.ReviewStatus;
import com.vulnshop.service.AuditService;
import com.vulnshop.service.OrderService;
import com.vulnshop.service.ProductService;
import com.vulnshop.service.ReviewService;
import com.vulnshop.service.UserService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

// VULN: Missing Function-Level Access Control - /admin/** is authenticated-only in SecurityConfig,
// no @PreAuthorize("hasRole('ADMIN')") here or in SecurityConfig. Any authenticated user can access.
@RestController
@RequestMapping("/admin")
public class AdminController {

    private final UserService userService;
    private final OrderService orderService;
    private final ReviewService reviewService;
    private final AuditService auditService;
    private final ProductService productService;

    public AdminController(UserService userService, OrderService orderService,
                           ReviewService reviewService, AuditService auditService,
                           ProductService productService) {
        this.userService = userService;
        this.orderService = orderService;
        this.reviewService = reviewService;
        this.auditService = auditService;
        this.productService = productService;
    }

    @GetMapping("/dashboard")
    public ResponseEntity<DashboardStatsResponse> getDashboard() {
        return ResponseEntity.ok(userService.getDashboardStats());
    }

    @GetMapping("/users")
    public ResponseEntity<List<UserResponse>> getAllUsers() {
        return ResponseEntity.ok(userService.getAllUsers());
    }

    @GetMapping("/orders")
    public ResponseEntity<List<OrderResponse>> getAllOrders() {
        return ResponseEntity.ok(orderService.getAllOrders());
    }

    @GetMapping("/orders/{id}")
    public ResponseEntity<OrderResponse> getOrderById(@PathVariable Long id) {
        return ResponseEntity.ok(orderService.getOrderById(id));
    }

    @PutMapping("/orders/{id}/status")
    public ResponseEntity<OrderResponse> updateOrderStatus(@PathVariable Long id,
                                                            @RequestBody OrderStatusUpdateRequest request) {
        return ResponseEntity.ok(orderService.updateOrderStatus(id, request));
    }

    @GetMapping("/reviews")
    public ResponseEntity<List<ReviewResponse>> getPendingReviews() {
        return ResponseEntity.ok(reviewService.getPendingReviews());
    }

    @PutMapping("/reviews/{id}/status")
    public ResponseEntity<ReviewResponse> updateReviewStatus(@PathVariable Long id,
                                                              @RequestParam ReviewStatus status) {
        return ResponseEntity.ok(reviewService.updateReviewStatus(id, status));
    }

    @GetMapping("/audit-logs")
    public ResponseEntity<List<AuditLog>> getAuditLogs() {
        // AuditLogRepository.findByUserId(null) won't return all — use findAll via JpaRepository
        return ResponseEntity.ok(auditService.getAllAuditLogs());
    }

    @GetMapping("/products")
    public ResponseEntity<PageResponse<ProductResponse>> getAllProducts() {
        return ResponseEntity.ok(productService.getAllProducts(new ProductSearchRequest()));
    }
}
