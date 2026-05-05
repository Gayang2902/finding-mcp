package com.vulnshop.service;

import com.vulnshop.dto.request.CouponCreateRequest;
import com.vulnshop.dto.response.CouponResponse;
import com.vulnshop.entity.Coupon;
import com.vulnshop.entity.DiscountType;
import com.vulnshop.exception.BadRequestException;
import com.vulnshop.exception.InvalidCouponException;
import com.vulnshop.exception.ResourceNotFoundException;
import com.vulnshop.repository.CouponRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional
public class CouponService {

    private final CouponRepository couponRepository;

    public CouponService(CouponRepository couponRepository) {
        this.couponRepository = couponRepository;
    }

    public CouponResponse createCoupon(CouponCreateRequest request) {
        if (couponRepository.findByCode(request.getCode()).isPresent()) {
            throw new BadRequestException("Coupon code already exists: " + request.getCode());
        }
        Coupon coupon = Coupon.builder()
                .code(request.getCode().toUpperCase())
                .description(request.getDescription())
                .discountType(request.getDiscountType())
                .discountValue(request.getDiscountValue())
                .minimumOrderAmount(request.getMinimumOrderAmount())
                .maximumDiscount(request.getMaximumDiscount())
                .usageLimit(request.getUsageLimit())
                .validFrom(request.getValidFrom())
                .validUntil(request.getValidUntil())
                .applicableCategories(request.getApplicableCategories() != null ? request.getApplicableCategories() : List.of())
                .build();
        return mapToResponse(couponRepository.save(coupon));
    }

    @Transactional(readOnly = true)
    public Coupon validateCoupon(String code, BigDecimal orderTotal) {
        Coupon coupon = couponRepository.findByCode(code.toUpperCase())
                .orElseThrow(() -> new InvalidCouponException("Invalid coupon code: " + code));

        if (!coupon.isActive()) {
            throw new InvalidCouponException("Coupon is not active");
        }
        LocalDateTime now = LocalDateTime.now();
        if (now.isBefore(coupon.getValidFrom()) || now.isAfter(coupon.getValidUntil())) {
            throw new InvalidCouponException("Coupon has expired or is not yet valid");
        }
        if (coupon.getUsageLimit() != null && coupon.getUsageCount() >= coupon.getUsageLimit()) {
            throw new InvalidCouponException("Coupon usage limit has been reached");
        }
        if (coupon.getMinimumOrderAmount() != null &&
                orderTotal.compareTo(coupon.getMinimumOrderAmount()) < 0) {
            throw new InvalidCouponException("Order total does not meet minimum amount of " + coupon.getMinimumOrderAmount());
        }
        return coupon;
    }

    // VULN: Business Logic - no per-user usage tracking, usage count increment is non-atomic
    // Same coupon can be applied multiple times by the same user
    public BigDecimal applyCoupon(String code, BigDecimal orderTotal) {
        Coupon coupon = validateCoupon(code, orderTotal);

        BigDecimal discount;
        if (coupon.getDiscountType() == DiscountType.PERCENTAGE) {
            discount = orderTotal.multiply(coupon.getDiscountValue())
                    .divide(BigDecimal.valueOf(100), 2, RoundingMode.HALF_UP);
        } else {
            discount = coupon.getDiscountValue();
        }

        if (coupon.getMaximumDiscount() != null && discount.compareTo(coupon.getMaximumDiscount()) > 0) {
            discount = coupon.getMaximumDiscount();
        }
        if (discount.compareTo(orderTotal) > 0) {
            discount = orderTotal;
        }

        // VULN: non-atomic increment - read-modify-write without locking
        coupon.setUsageCount(coupon.getUsageCount() + 1);
        couponRepository.save(coupon);

        return discount;
    }

    @Transactional(readOnly = true)
    public List<CouponResponse> getActiveCoupons() {
        return couponRepository.findByIsActiveTrue().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    public CouponResponse deactivateCoupon(Long couponId) {
        Coupon coupon = couponRepository.findById(couponId)
                .orElseThrow(() -> new ResourceNotFoundException("Coupon not found: " + couponId));
        coupon.setActive(false);
        return mapToResponse(couponRepository.save(coupon));
    }

    public CouponResponse mapToResponse(Coupon coupon) {
        return CouponResponse.builder()
                .id(coupon.getId())
                .code(coupon.getCode())
                .description(coupon.getDescription())
                .discountType(coupon.getDiscountType())
                .discountValue(coupon.getDiscountValue())
                .minimumOrderAmount(coupon.getMinimumOrderAmount())
                .maximumDiscount(coupon.getMaximumDiscount())
                .validFrom(coupon.getValidFrom())
                .validUntil(coupon.getValidUntil())
                .isActive(coupon.isActive())
                .build();
    }
}
