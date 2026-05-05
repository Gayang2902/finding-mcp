package com.vulnshop.controller;

import com.vulnshop.dto.request.ApplyCouponRequest;
import com.vulnshop.dto.request.CouponCreateRequest;
import com.vulnshop.dto.response.CouponResponse;
import com.vulnshop.entity.Coupon;
import com.vulnshop.service.CouponService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/coupons")
public class CouponController {

    private final CouponService couponService;

    public CouponController(CouponService couponService) {
        this.couponService = couponService;
    }

    // VULN: Missing access control - should be admin only
    @PostMapping("/")
    public ResponseEntity<CouponResponse> createCoupon(@Valid @RequestBody CouponCreateRequest request) {
        return ResponseEntity.status(HttpStatus.CREATED).body(couponService.createCoupon(request));
    }

    // VULN: Business Logic - can apply the same coupon multiple times, no per-user usage tracking
    // applyCoupon() returns BigDecimal (the discount amount)
    @PostMapping("/apply")
    public ResponseEntity<Map<String, Object>> applyCoupon(@Valid @RequestBody ApplyCouponRequest request,
                                                            @RequestParam(required = false, defaultValue = "0") BigDecimal orderTotal) {
        BigDecimal discount = couponService.applyCoupon(request.getCode(), orderTotal);
        return ResponseEntity.ok(Map.of("code", request.getCode(), "discount", discount));
    }

    // validateCoupon() returns Coupon entity; map it via the service helper
    @PostMapping("/validate")
    public ResponseEntity<CouponResponse> validateCoupon(@Valid @RequestBody ApplyCouponRequest request,
                                                          @RequestParam(required = false, defaultValue = "0") BigDecimal orderTotal) {
        Coupon coupon = couponService.validateCoupon(request.getCode(), orderTotal);
        return ResponseEntity.ok(couponService.mapToResponse(coupon));
    }

    // VULN: Missing access control - should be admin only, exposes all coupon codes
    @GetMapping("/")
    public ResponseEntity<List<CouponResponse>> getActiveCoupons() {
        return ResponseEntity.ok(couponService.getActiveCoupons());
    }
}
