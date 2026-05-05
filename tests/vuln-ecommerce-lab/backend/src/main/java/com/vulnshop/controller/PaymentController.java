package com.vulnshop.controller;

import com.vulnshop.dto.request.PaymentRequest;
import com.vulnshop.dto.response.PaymentResponse;
import com.vulnshop.security.SecurityUtils;
import com.vulnshop.service.PaymentService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/payments")
public class PaymentController {

    private final PaymentService paymentService;

    public PaymentController(PaymentService paymentService) {
        this.paymentService = paymentService;
    }

    // VULN: Parameter Tampering - amount comes from client request body, not computed server-side
    @PostMapping("/")
    public ResponseEntity<PaymentResponse> processPayment(@Valid @RequestBody PaymentRequest request) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(paymentService.processPayment(currentUserId, request));
    }

    // VULN: IDOR - no ownership check, any user can retrieve any payment by ID
    @GetMapping("/{id}")
    public ResponseEntity<PaymentResponse> getPaymentById(@PathVariable Long id) {
        return ResponseEntity.ok(paymentService.getPaymentById(id));
    }

    @GetMapping("/user")
    public ResponseEntity<List<PaymentResponse>> getPaymentsByUser() {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(paymentService.getPaymentsByUser(currentUserId));
    }

    // VULN: IDOR - no ownership check, any user can refund any payment by ID
    @PostMapping("/{id}/refund")
    public ResponseEntity<PaymentResponse> refundPayment(@PathVariable Long id) {
        return ResponseEntity.ok(paymentService.refundPayment(id));
    }
}
