package com.vulnshop.controller;

import com.vulnshop.dto.request.CartItemRequest;
import com.vulnshop.dto.request.CartUpdateRequest;
import com.vulnshop.dto.response.CartResponse;
import com.vulnshop.security.SecurityUtils;
import com.vulnshop.service.CartService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;

@RestController
@RequestMapping("/cart")
public class CartController {

    private final CartService cartService;

    public CartController(CartService cartService) {
        this.cartService = cartService;
    }

    @GetMapping("/")
    public ResponseEntity<CartResponse> getCart() {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(cartService.getCart(currentUserId));
    }

    // VULN: Parameter Tampering - client can supply a priceOverride to bypass real pricing
    @PostMapping("/items")
    public ResponseEntity<CartResponse> addItem(@Valid @RequestBody CartItemRequest request,
                                                @RequestParam(required = false) BigDecimal priceOverride) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(cartService.addItem(currentUserId, request, priceOverride));
    }

    // VULN: IDOR - no check that itemId belongs to currentUser's cart
    @PutMapping("/items/{itemId}")
    public ResponseEntity<CartResponse> updateItemQuantity(@PathVariable Long itemId,
                                                           @Valid @RequestBody CartUpdateRequest request) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(cartService.updateItemQuantity(currentUserId, itemId, request));
    }

    // VULN: IDOR - no check that itemId belongs to currentUser's cart
    @DeleteMapping("/items/{itemId}")
    public ResponseEntity<CartResponse> removeItem(@PathVariable Long itemId) {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(cartService.removeItem(currentUserId, itemId));
    }

    @DeleteMapping("/")
    public ResponseEntity<Void> clearCart() {
        Long currentUserId = SecurityUtils.getCurrentUserId();
        cartService.clearCart(currentUserId);
        return ResponseEntity.noContent().build();
    }
}
