package com.vulnshop.service;

import com.vulnshop.dto.request.CartItemRequest;
import com.vulnshop.dto.request.CartUpdateRequest;
import com.vulnshop.dto.response.CartItemResponse;
import com.vulnshop.dto.response.CartResponse;
import com.vulnshop.entity.Cart;
import com.vulnshop.entity.CartItem;
import com.vulnshop.entity.Product;
import com.vulnshop.entity.User;
import com.vulnshop.exception.BadRequestException;
import com.vulnshop.exception.InsufficientStockException;
import com.vulnshop.exception.ResourceNotFoundException;
import com.vulnshop.repository.CartItemRepository;
import com.vulnshop.repository.CartRepository;
import com.vulnshop.repository.ProductRepository;
import com.vulnshop.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional
public class CartService {

    private final CartRepository cartRepository;
    private final CartItemRepository cartItemRepository;
    private final ProductRepository productRepository;
    private final UserRepository userRepository;

    public CartService(CartRepository cartRepository,
                       CartItemRepository cartItemRepository,
                       ProductRepository productRepository,
                       UserRepository userRepository) {
        this.cartRepository = cartRepository;
        this.cartItemRepository = cartItemRepository;
        this.productRepository = productRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public CartResponse getCart(Long userId) {
        Cart cart = cartRepository.findByUserId(userId).orElseGet(() -> {
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));
            Cart newCart = Cart.builder().user(user).build();
            return cartRepository.save(newCart);
        });
        return mapToResponse(cart);
    }

    // VULN: Parameter Tampering - accepts an optional priceOverride parameter.
    // If priceOverride is not null, uses it instead of the product's real price.
    // This allows clients to set arbitrary prices for cart items.
    @Transactional
    public CartResponse addItem(Long userId, CartItemRequest request, BigDecimal priceOverride) {
        Cart cart = cartRepository.findByUserId(userId).orElseGet(() -> {
            User user = userRepository.findById(userId)
                    .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));
            Cart newCart = Cart.builder().user(user).build();
            return cartRepository.save(newCart);
        });

        Product product = productRepository.findById(request.getProductId())
                .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + request.getProductId()));

        if (!product.isActive()) {
            throw new BadRequestException("Product is not available");
        }
        if (product.getStock() < request.getQuantity()) {
            throw new InsufficientStockException("Insufficient stock for product: " + product.getName());
        }

        // VULN: uses client-supplied priceOverride if provided, instead of product.getPrice()
        BigDecimal priceToUse = (priceOverride != null) ? priceOverride : product.getPrice();

        // Check if item already in cart
        cartItemRepository.findByCartIdAndProductId(cart.getId(), product.getId())
                .ifPresentOrElse(existing -> {
                    existing.setQuantity(existing.getQuantity() + request.getQuantity());
                    existing.setPriceAtAdd(priceToUse);
                    cartItemRepository.save(existing);
                }, () -> {
                    CartItem item = CartItem.builder()
                            .cart(cart)
                            .product(product)
                            .quantity(request.getQuantity())
                            .priceAtAdd(priceToUse)
                            .build();
                    cartItemRepository.save(item);
                });

        return getCart(userId);
    }

    // VULN: IDOR - finds CartItem by cartItemId WITHOUT verifying it belongs to the user's cart
    @Transactional
    public CartResponse updateItemQuantity(Long userId, Long cartItemId, CartUpdateRequest request) {
        CartItem item = cartItemRepository.findById(cartItemId)
                .orElseThrow(() -> new ResourceNotFoundException("Cart item not found: " + cartItemId));

        if (request.getQuantity() <= 0) {
            throw new BadRequestException("Quantity must be at least 1");
        }

        Product product = item.getProduct();
        if (product.getStock() < request.getQuantity()) {
            throw new InsufficientStockException("Insufficient stock for product: " + product.getName());
        }

        item.setQuantity(request.getQuantity());
        cartItemRepository.save(item);

        return getCart(userId);
    }

    // VULN: IDOR - removes cart item without verifying it belongs to the user's cart
    @Transactional
    public CartResponse removeItem(Long userId, Long cartItemId) {
        CartItem item = cartItemRepository.findById(cartItemId)
                .orElseThrow(() -> new ResourceNotFoundException("Cart item not found: " + cartItemId));
        cartItemRepository.delete(item);
        return getCart(userId);
    }

    @Transactional
    public void clearCart(Long userId) {
        cartRepository.findByUserId(userId).ifPresent(cart -> {
            cart.getItems().clear();
            cartRepository.save(cart);
        });
    }

    @Transactional(readOnly = true)
    public BigDecimal getCartTotal(Long userId) {
        return cartRepository.findByUserId(userId)
                .map(Cart::getTotalPrice)
                .orElse(BigDecimal.ZERO);
    }

    public CartResponse mapToResponse(Cart cart) {
        List<CartItemResponse> items = cart.getItems().stream()
                .map(this::mapItemToResponse)
                .collect(Collectors.toList());

        BigDecimal total = cart.getTotalPrice();

        return CartResponse.builder()
                .id(cart.getId())
                .items(items)
                .totalPrice(total)
                .itemCount(items.size())
                .build();
    }

    private CartItemResponse mapItemToResponse(CartItem item) {
        Product product = item.getProduct();
        BigDecimal subtotal = item.getPriceAtAdd().multiply(BigDecimal.valueOf(item.getQuantity()));
        return CartItemResponse.builder()
                .id(item.getId())
                .productId(product != null ? product.getId() : null)
                .productName(product != null ? product.getName() : null)
                .productImageUrl(product != null ? product.getImageUrl() : null)
                .productPrice(product != null ? product.getPrice() : null)
                .quantity(item.getQuantity())
                .priceAtAdd(item.getPriceAtAdd())
                .subtotal(subtotal)
                .build();
    }
}
