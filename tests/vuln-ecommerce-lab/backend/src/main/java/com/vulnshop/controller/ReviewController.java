package com.vulnshop.controller;

import com.vulnshop.dto.request.ReviewCreateRequest;
import com.vulnshop.dto.response.ReviewResponse;
import com.vulnshop.security.SecurityUtils;
import com.vulnshop.service.ReviewService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/reviews")
public class ReviewController {

    private final ReviewService reviewService;

    public ReviewController(ReviewService reviewService) {
        this.reviewService = reviewService;
    }

    @PostMapping("/")
    public ResponseEntity<ReviewResponse> createReview(@Valid @RequestBody ReviewCreateRequest request) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(reviewService.createReview(currentUserId, request));
    }

    @GetMapping("/product/{productId}")
    public ResponseEntity<List<ReviewResponse>> getProductReviews(@PathVariable Long productId) {
        return ResponseEntity.ok(reviewService.getProductReviews(productId));
    }

    @GetMapping("/user")
    public ResponseEntity<List<ReviewResponse>> getUserReviews() {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(reviewService.getUserReviews(currentUserId));
    }

    // VULN: IDOR - no ownership check, any authenticated user can delete any review
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteReview(@PathVariable Long id) {
        reviewService.deleteReview(id);
        return ResponseEntity.noContent().build();
    }

    @PutMapping("/{id}/helpful")
    public ResponseEntity<ReviewResponse> markHelpful(@PathVariable Long id) {
        return ResponseEntity.ok(reviewService.markHelpful(id));
    }

    @PutMapping("/{id}/report")
    public ResponseEntity<ReviewResponse> reportReview(@PathVariable Long id) {
        return ResponseEntity.ok(reviewService.reportReview(id));
    }
}
