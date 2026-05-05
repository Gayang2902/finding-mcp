package com.vulnshop.service;

import com.vulnshop.dto.request.OrderCreateRequest;
import com.vulnshop.dto.request.OrderStatusUpdateRequest;
import com.vulnshop.dto.request.RefundRequest;
import com.vulnshop.dto.response.AddressResponse;
import com.vulnshop.dto.response.OrderItemResponse;
import com.vulnshop.dto.response.OrderResponse;
import com.vulnshop.dto.response.OrderSummaryResponse;
import com.vulnshop.dto.response.ShippingResponse;
import com.vulnshop.entity.*;
import com.vulnshop.exception.BadRequestException;
import com.vulnshop.exception.InsufficientStockException;
import com.vulnshop.exception.ResourceNotFoundException;
import com.vulnshop.repository.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional
public class OrderService {

    private final OrderRepository orderRepository;
    private final UserRepository userRepository;
    private final ProductRepository productRepository;
    private final AddressRepository addressRepository;
    private final ShippingInfoRepository shippingInfoRepository;
    private final CouponService couponService;
    private final ShippingService shippingService;

    public OrderService(OrderRepository orderRepository,
                        UserRepository userRepository,
                        ProductRepository productRepository,
                        AddressRepository addressRepository,
                        ShippingInfoRepository shippingInfoRepository,
                        CouponService couponService,
                        ShippingService shippingService) {
        this.orderRepository = orderRepository;
        this.userRepository = userRepository;
        this.productRepository = productRepository;
        this.addressRepository = addressRepository;
        this.shippingInfoRepository = shippingInfoRepository;
        this.couponService = couponService;
        this.shippingService = shippingService;
    }

    // VULN: IDOR - finds order by ID without checking if it belongs to the requesting user
    @Transactional(readOnly = true)
    public OrderResponse getOrderById(Long orderId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + orderId));
        return mapToResponse(order);
    }

    // VULN: IDOR - returns order without ownership check
    @Transactional(readOnly = true)
    public OrderResponse getOrderByNumber(String orderNumber) {
        Order order = orderRepository.findByOrderNumber(orderNumber)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + orderNumber));
        return mapToResponse(order);
    }

    public OrderResponse createOrder(Long userId, OrderCreateRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));

        Address shippingAddress = addressRepository.findById(request.getShippingAddressId())
                .orElseThrow(() -> new ResourceNotFoundException("Shipping address not found: " + request.getShippingAddressId()));

        Address billingAddress = null;
        if (request.getBillingAddressId() != null) {
            billingAddress = addressRepository.findById(request.getBillingAddressId())
                    .orElseThrow(() -> new ResourceNotFoundException("Billing address not found: " + request.getBillingAddressId()));
        }

        // Validate stock and build order items
        List<OrderItem> orderItems = new ArrayList<>();
        BigDecimal subtotal = BigDecimal.ZERO;

        for (var itemRequest : request.getItems()) {
            Product product = productRepository.findById(itemRequest.getProductId())
                    .orElseThrow(() -> new ResourceNotFoundException("Product not found: " + itemRequest.getProductId()));

            if (!product.isActive()) {
                throw new BadRequestException("Product is not available: " + product.getName());
            }
            if (product.getStock() < itemRequest.getQuantity()) {
                throw new InsufficientStockException(
                        "Insufficient stock for product: " + product.getName() +
                        ". Available: " + product.getStock() + ", Requested: " + itemRequest.getQuantity());
            }

            BigDecimal unitPrice = product.getPrice();
            BigDecimal itemTotal = unitPrice.multiply(BigDecimal.valueOf(itemRequest.getQuantity()));
            subtotal = subtotal.add(itemTotal);

            OrderItem orderItem = OrderItem.builder()
                    .product(product)
                    .productName(product.getName())
                    .productSku(product.getSku())
                    .quantity(itemRequest.getQuantity())
                    .unitPrice(unitPrice)
                    .totalPrice(itemTotal)
                    .discount(BigDecimal.ZERO)
                    .build();
            orderItems.add(orderItem);
        }

        // Apply coupon discount
        BigDecimal discountAmount = BigDecimal.ZERO;
        if (request.getCouponCode() != null && !request.getCouponCode().isBlank()) {
            discountAmount = couponService.applyCoupon(request.getCouponCode(), subtotal);
        }

        // Calculate tax (10%) and shipping
        BigDecimal taxableAmount = subtotal.subtract(discountAmount);
        BigDecimal taxAmount = taxableAmount.multiply(new BigDecimal("0.10"))
                .setScale(2, RoundingMode.HALF_UP);
        BigDecimal shippingCost = subtotal.compareTo(new BigDecimal("50")) >= 0
                ? BigDecimal.ZERO : new BigDecimal("9.99");
        BigDecimal totalAmount = subtotal.subtract(discountAmount).add(taxAmount).add(shippingCost);

        String orderNumber = "ORD-" + UUID.randomUUID().toString().substring(0, 8).toUpperCase();

        Order order = Order.builder()
                .orderNumber(orderNumber)
                .user(user)
                .shippingAddress(shippingAddress)
                .billingAddress(billingAddress != null ? billingAddress : shippingAddress)
                .status(OrderStatus.PENDING)
                .subtotal(subtotal)
                .shippingCost(shippingCost)
                .taxAmount(taxAmount)
                .discountAmount(discountAmount)
                .totalAmount(totalAmount)
                .couponCode(request.getCouponCode())
                .paymentMethod(request.getPaymentMethod())
                .paymentStatus(PaymentStatus.PENDING)
                .notes(request.getNotes())
                .build();

        Order savedOrder = orderRepository.save(order);

        // Link items to order and reduce stock
        for (int i = 0; i < orderItems.size(); i++) {
            OrderItem item = orderItems.get(i);
            item.setOrder(savedOrder);
            savedOrder.getItems().add(item);

            // Reduce stock
            Product product = productRepository.findById(request.getItems().get(i).getProductId()).get();
            product.setStock(product.getStock() - request.getItems().get(i).getQuantity());
            productRepository.save(product);
        }

        orderRepository.save(savedOrder);

        // Create shipping info
        shippingService.createShippingInfo(savedOrder);

        return mapToResponse(savedOrder);
    }

    @Transactional(readOnly = true)
    public List<OrderSummaryResponse> getUserOrders(Long userId) {
        return orderRepository.findByUserId(userId).stream()
                .map(this::mapToSummary)
                .collect(Collectors.toList());
    }

    // VULN: no role check - any authenticated user can update any order status
    public OrderResponse updateOrderStatus(Long orderId, OrderStatusUpdateRequest request) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + orderId));
        order.setStatus(request.getStatus());
        if (request.getTrackingNumber() != null) order.setTrackingNumber(request.getTrackingNumber());
        if (request.getNotes() != null) order.setNotes(request.getNotes());
        return mapToResponse(orderRepository.save(order));
    }

    // VULN: no ownership check - cancels any order without verifying the requesting user owns it
    public OrderResponse cancelOrder(Long orderId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + orderId));
        if (order.getStatus() == OrderStatus.DELIVERED || order.getStatus() == OrderStatus.CANCELLED) {
            throw new BadRequestException("Order cannot be cancelled in its current state: " + order.getStatus());
        }
        order.setStatus(OrderStatus.CANCELLED);

        // Restore stock
        for (OrderItem item : order.getItems()) {
            if (item.getProduct() != null) {
                Product product = item.getProduct();
                product.setStock(product.getStock() + item.getQuantity());
                productRepository.save(product);
            }
        }

        return mapToResponse(orderRepository.save(order));
    }

    // VULN: IDOR - returns tracking info without auth check
    @Transactional(readOnly = true)
    public OrderResponse getOrderTracking(Long orderId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + orderId));
        return mapToResponse(order);
    }

    // VULN: no ownership check - processes refund without verifying user owns the order
    public OrderResponse processRefund(RefundRequest request) {
        Order order = orderRepository.findById(request.getOrderId())
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + request.getOrderId()));
        order.setPaymentStatus(PaymentStatus.REFUNDED);
        order.setStatus(OrderStatus.CANCELLED);
        order.setNotes("Refund reason: " + request.getReason());
        return mapToResponse(orderRepository.save(order));
    }

    @Transactional(readOnly = true)
    public List<OrderResponse> getAllOrders() {
        return orderRepository.findAll().stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    public OrderResponse mapToResponse(Order order) {
        List<OrderItemResponse> items = order.getItems().stream()
                .map(item -> OrderItemResponse.builder()
                        .id(item.getId())
                        .productId(item.getProduct() != null ? item.getProduct().getId() : null)
                        .productName(item.getProductName())
                        .productSku(item.getProductSku())
                        .productImageUrl(item.getProduct() != null ? item.getProduct().getImageUrl() : null)
                        .quantity(item.getQuantity())
                        .unitPrice(item.getUnitPrice())
                        .totalPrice(item.getTotalPrice())
                        .discount(item.getDiscount())
                        .build())
                .collect(Collectors.toList());

        AddressResponse shippingAddr = order.getShippingAddress() != null
                ? mapAddress(order.getShippingAddress()) : null;
        AddressResponse billingAddr = order.getBillingAddress() != null
                ? mapAddress(order.getBillingAddress()) : null;

        ShippingResponse shippingInfo = null;
        try {
            shippingInfo = shippingInfoRepository.findByOrderId(order.getId())
                    .map(shippingService::mapToResponse)
                    .orElse(null);
        } catch (Exception ignored) {
            // shipping info may not exist yet
        }

        return OrderResponse.builder()
                .id(order.getId())
                .orderNumber(order.getOrderNumber())
                .status(order.getStatus())
                .items(items)
                .shippingAddress(shippingAddr)
                .billingAddress(billingAddr)
                .shippingInfo(shippingInfo)
                .subtotal(order.getSubtotal())
                .shippingCost(order.getShippingCost())
                .taxAmount(order.getTaxAmount())
                .discountAmount(order.getDiscountAmount())
                .totalAmount(order.getTotalAmount())
                .couponCode(order.getCouponCode())
                .paymentMethod(order.getPaymentMethod())
                .paymentStatus(order.getPaymentStatus())
                .trackingNumber(order.getTrackingNumber())
                .notes(order.getNotes())
                .createdAt(order.getCreatedAt())
                .updatedAt(order.getUpdatedAt())
                .build();
    }

    public OrderSummaryResponse mapToSummary(Order order) {
        return OrderSummaryResponse.builder()
                .id(order.getId())
                .orderNumber(order.getOrderNumber())
                .totalAmount(order.getTotalAmount())
                .status(order.getStatus())
                .createdAt(order.getCreatedAt())
                .itemCount(order.getItems().size())
                .build();
    }

    private AddressResponse mapAddress(Address address) {
        return AddressResponse.builder()
                .id(address.getId())
                .label(address.getLabel())
                .fullName(address.getFullName())
                .streetAddress(address.getStreetAddress())
                .streetAddress2(address.getStreetAddress2())
                .city(address.getCity())
                .state(address.getState())
                .zipCode(address.getZipCode())
                .country(address.getCountry())
                .phone(address.getPhone())
                .isDefault(address.isDefault())
                .build();
    }
}
