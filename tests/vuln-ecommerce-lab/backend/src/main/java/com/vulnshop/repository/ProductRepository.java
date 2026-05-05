package com.vulnshop.repository;

import com.vulnshop.entity.Product;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.List;

@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {

    List<Product> findByCategoryId(Long categoryId);

    List<Product> findBySellerIdAndIsActive(Long sellerId, boolean isActive);

    List<Product> findByIsActiveTrue();

    @Query("SELECT p FROM Product p WHERE p.isActive = true AND (p.name LIKE %:query% OR p.description LIKE %:query%)")
    List<Product> searchByNameOrDescription(@Param("query") String query);

    List<Product> findTopByOrderByAverageRatingDesc();
}
