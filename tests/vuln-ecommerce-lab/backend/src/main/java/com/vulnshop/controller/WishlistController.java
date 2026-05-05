package com.vulnshop.controller;

import com.vulnshop.dto.response.ProductResponse;
import com.vulnshop.entity.WishlistItem;
import com.vulnshop.security.SecurityUtils;
import com.vulnshop.service.ProductService;
import com.vulnshop.service.WishlistService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/wishlist")
public class WishlistController {

    private final WishlistService wishlistService;
    private final ProductService productService;

    public WishlistController(WishlistService wishlistService, ProductService productService) {
        this.wishlistService = wishlistService;
        this.productService = productService;
    }

    @GetMapping("/")
    public ResponseEntity<List<ProductResponse>> getUserWishlist() {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        List<WishlistItem> items = wishlistService.getUserWishlist(currentUserId);
        List<ProductResponse> products = items.stream()
                .map(item -> productService.mapToResponse(item.getProduct()))
                .collect(Collectors.toList());
        return ResponseEntity.ok(products);
    }

    @PostMapping("/{productId}")
    public ResponseEntity<Void> addToWishlist(@PathVariable Long productId) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        wishlistService.addToWishlist(currentUserId, productId);
        return ResponseEntity.ok().build();
    }

    // VULN: IDOR - path variable is passed directly as wishlistItemId to the service,
    // not as productId. Any authenticated user can delete any wishlist item by guessing the ID.
    @DeleteMapping("/{productId}")
    public ResponseEntity<Void> removeFromWishlist(@PathVariable Long productId) {
        wishlistService.removeFromWishlist(productId);
        return ResponseEntity.noContent().build();
    }
}
