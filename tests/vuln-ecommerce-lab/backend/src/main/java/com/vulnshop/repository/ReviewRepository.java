package com.vulnshop.repository;

import com.vulnshop.entity.Review;
import com.vulnshop.entity.ReviewStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ReviewRepository extends JpaRepository<Review, Long> {

    List<Review> findByProductId(Long productId);

    List<Review> findByUserId(Long userId);

    List<Review> findByProductIdAndStatus(Long productId, ReviewStatus status);

    boolean existsByUserIdAndProductId(Long userId, Long productId);
}
