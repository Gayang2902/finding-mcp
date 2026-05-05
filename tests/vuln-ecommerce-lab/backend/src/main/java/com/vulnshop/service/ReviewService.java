package com.vulnshop.service;

import com.vulnshop.dto.request.ReviewCreateRequest;
import com.vulnshop.dto.response.ReviewResponse;
import com.vulnshop.entity.Product;
import com.vulnshop.entity.Review;
import com.vulnshop.entity.ReviewStatus;
import com.vulnshop.entity.User;
import com.vulnshop.exception.BadRequestException;
import com.vulnshop.exception.ResourceNotFoundException;
import com.vulnshop.repository.ProductRepository;
import com.vulnshop.repository.ReviewRepository;
import com.vulnshop.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional
public class ReviewService {

    private final ReviewRepository reviewRepository;
    private final UserRepository userRepository;
    private final ProductRepository productRepository;

    public ReviewService(ReviewRepository reviewRepository,
                         UserRepository userRepository,
                         ProductRepository productRepository) {
        this.reviewRepository = reviewRepository;
        this.userRepository = userRepository;
        this.productRepository = productRepository;
    }

    // VULN: no verified purchase check - does not verify if the user actually bought the product
    public ReviewResponse createReview(Long userId, ReviewCreateRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));
        Product product = productRepository.findById(request.getProductId())
                .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + request.getProductId()));

        if (reviewRepository.existsByUserIdAndProductId(userId, request.getProductId())) {
            throw new BadRequestException("You have already reviewed this product");
        }

        Review review = Review.builder()
                .user(user)
                .product(product)
                .rating(request.getRating())
                .title(request.getTitle())
                .comment(request.getComment())
                .isVerifiedPurchase(false) // VULN: always false, no purchase check
                .status(ReviewStatus.PENDING)
                .build();

        Review saved = reviewRepository.save(review);

        // Update product average rating
        List<Review> allReviews = reviewRepository.findByProductId(product.getId());
        double avg = allReviews.stream().mapToInt(Review::getRating).average().orElse(0.0);
        product.setAverageRating(avg);
        product.setReviewCount(allReviews.size());
        productRepository.save(product);

        return mapToResponse(saved);
    }

    @Transactional(readOnly = true)
    public List<ReviewResponse> getProductReviews(Long productId) {
        return reviewRepository.findByProductIdAndStatus(productId, ReviewStatus.APPROVED).stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public List<ReviewResponse> getUserReviews(Long userId) {
        return reviewRepository.findByUserId(userId).stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    // VULN: IDOR - deletes any review by ID without checking ownership
    public void deleteReview(Long reviewId) {
        Review review = reviewRepository.findById(reviewId)
                .orElseThrow(() -> new ResourceNotFoundException("Review not found: " + reviewId));
        reviewRepository.delete(review);
    }

    @Transactional(readOnly = true)
    public List<ReviewResponse> getPendingReviews() {
        return reviewRepository.findAll().stream()
                .filter(r -> r.getStatus() == ReviewStatus.PENDING)
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    public ReviewResponse updateReviewStatus(Long reviewId, ReviewStatus status) {
        Review review = reviewRepository.findById(reviewId)
                .orElseThrow(() -> new ResourceNotFoundException("Review not found: " + reviewId));
        review.setStatus(status);
        return mapToResponse(reviewRepository.save(review));
    }

    public ReviewResponse markHelpful(Long reviewId) {
        Review review = reviewRepository.findById(reviewId)
                .orElseThrow(() -> new ResourceNotFoundException("Review not found: " + reviewId));
        review.setHelpfulCount(review.getHelpfulCount() + 1);
        return mapToResponse(reviewRepository.save(review));
    }

    public ReviewResponse reportReview(Long reviewId) {
        Review review = reviewRepository.findById(reviewId)
                .orElseThrow(() -> new ResourceNotFoundException("Review not found: " + reviewId));
        review.setReportCount(review.getReportCount() + 1);
        return mapToResponse(reviewRepository.save(review));
    }

    public ReviewResponse mapToResponse(Review review) {
        String userName = review.getUser() != null ?
                review.getUser().getFirstName() + " " + review.getUser().getLastName() : "Unknown";
        return ReviewResponse.builder()
                .id(review.getId())
                .userId(review.getUser() != null ? review.getUser().getId() : null)
                .userName(userName)
                .rating(review.getRating())
                .title(review.getTitle())
                .comment(review.getComment())
                .isVerifiedPurchase(review.isVerifiedPurchase())
                .helpfulCount(review.getHelpfulCount())
                .createdAt(review.getCreatedAt())
                .build();
    }
}
