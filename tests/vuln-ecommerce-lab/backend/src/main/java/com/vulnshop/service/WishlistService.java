package com.vulnshop.service;

import com.vulnshop.entity.Product;
import com.vulnshop.entity.User;
import com.vulnshop.entity.WishlistItem;
import com.vulnshop.exception.BadRequestException;
import com.vulnshop.exception.ResourceNotFoundException;
import com.vulnshop.repository.ProductRepository;
import com.vulnshop.repository.UserRepository;
import com.vulnshop.repository.WishlistItemRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Transactional
public class WishlistService {

    private final WishlistItemRepository wishlistItemRepository;
    private final UserRepository userRepository;
    private final ProductRepository productRepository;

    public WishlistService(WishlistItemRepository wishlistItemRepository,
                           UserRepository userRepository,
                           ProductRepository productRepository) {
        this.wishlistItemRepository = wishlistItemRepository;
        this.userRepository = userRepository;
        this.productRepository = productRepository;
    }

    public WishlistItem addToWishlist(Long userId, Long productId) {
        if (wishlistItemRepository.existsByUserIdAndProductId(userId, productId)) {
            throw new BadRequestException("Product already in wishlist");
        }
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));
        Product product = productRepository.findById(productId)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + productId));

        WishlistItem item = WishlistItem.builder()
                .user(user)
                .product(product)
                .build();
        return wishlistItemRepository.save(item);
    }

    // VULN: IDOR - removes any wishlist item by ID without checking ownership
    public void removeFromWishlist(Long wishlistItemId) {
        WishlistItem item = wishlistItemRepository.findById(wishlistItemId)
                .orElseThrow(() -> new ResourceNotFoundException("Wishlist item not found: " + wishlistItemId));
        wishlistItemRepository.delete(item);
    }

    @Transactional(readOnly = true)
    public List<WishlistItem> getUserWishlist(Long userId) {
        return wishlistItemRepository.findByUserId(userId);
    }

    @Transactional(readOnly = true)
    public boolean isInWishlist(Long userId, Long productId) {
        return wishlistItemRepository.existsByUserIdAndProductId(userId, productId);
    }
}
