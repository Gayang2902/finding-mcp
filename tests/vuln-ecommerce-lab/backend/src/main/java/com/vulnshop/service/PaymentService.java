package com.vulnshop.service;

import com.vulnshop.dto.request.PaymentRequest;
import com.vulnshop.dto.response.PaymentResponse;
import com.vulnshop.entity.Order;
import com.vulnshop.entity.Payment;
import com.vulnshop.entity.PaymentMethod;
import com.vulnshop.entity.PaymentStatus;
import com.vulnshop.entity.User;
import com.vulnshop.exception.PaymentFailedException;
import com.vulnshop.exception.ResourceNotFoundException;
import com.vulnshop.repository.OrderRepository;
import com.vulnshop.repository.PaymentRepository;
import com.vulnshop.repository.UserRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Random;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@Transactional
public class PaymentService {

    private final PaymentRepository paymentRepository;
    private final OrderRepository orderRepository;
    private final UserRepository userRepository;
    private final Random random = new Random();

    public PaymentService(PaymentRepository paymentRepository,
                          OrderRepository orderRepository,
                          UserRepository userRepository) {
        this.paymentRepository = paymentRepository;
        this.orderRepository = orderRepository;
        this.userRepository = userRepository;
    }

    // VULN: Parameter Tampering - trusts the amount field from the client request
    // instead of recalculating from the order total
    public PaymentResponse processPayment(Long userId, PaymentRequest request) {
        Order order = orderRepository.findById(request.getOrderId())
                .orElseThrow(() -> new ResourceNotFoundException("Order not found: " + request.getOrderId()));
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new ResourceNotFoundException("User not found: " + userId));

        // VULN: uses client-supplied amount instead of order.getTotalAmount()
        BigDecimal amountToCharge = request.getAmount();

        // Simulate 90% success rate
        boolean success = random.nextInt(10) < 9;

        String transactionId = UUID.randomUUID().toString();
        PaymentStatus status = success ? PaymentStatus.COMPLETED : PaymentStatus.FAILED;

        String cardLastFour = null;
        String cardBrand = null;
        if (request.getCardNumber() != null && request.getCardNumber().length() >= 4) {
            cardLastFour = request.getCardNumber().substring(request.getCardNumber().length() - 4);
            cardBrand = detectCardBrand(request.getCardNumber());
        }

        Payment payment = Payment.builder()
                .order(order)
                .user(user)
                .amount(amountToCharge)
                .method(request.getMethod())
                .status(status)
                .transactionId(transactionId)
                .cardLastFour(cardLastFour)
                .cardBrand(cardBrand)
                .gatewayResponse(success ? "Payment approved" : "Payment declined")
                .processedAt(LocalDateTime.now())
                .build();

        Payment saved = paymentRepository.save(payment);

        if (!success) {
            throw new PaymentFailedException("Payment processing failed. Transaction ID: " + transactionId);
        }

        // Update order payment status
        order.setPaymentStatus(PaymentStatus.COMPLETED);
        order.setPaymentMethod(request.getMethod());
        orderRepository.save(order);

        return mapToResponse(saved);
    }

    // VULN: IDOR - returns any payment without ownership check
    @Transactional(readOnly = true)
    public PaymentResponse getPaymentById(Long paymentId) {
        Payment payment = paymentRepository.findById(paymentId)
                .orElseThrow(() -> new ResourceNotFoundException("Payment not found: " + paymentId));
        return mapToResponse(payment);
    }

    @Transactional(readOnly = true)
    public List<PaymentResponse> getPaymentsByUser(Long userId) {
        return paymentRepository.findByUserId(userId).stream()
                .map(this::mapToResponse)
                .collect(Collectors.toList());
    }

    @Transactional(readOnly = true)
    public PaymentResponse getPaymentByTransaction(String transactionId) {
        Payment payment = paymentRepository.findByTransactionId(transactionId)
                .orElseThrow(() -> new ResourceNotFoundException("Payment not found for transaction: " + transactionId));
        return mapToResponse(payment);
    }

    // VULN: no ownership check - refunds any payment without verifying the requesting user owns it
    public PaymentResponse refundPayment(Long paymentId) {
        Payment payment = paymentRepository.findById(paymentId)
                .orElseThrow(() -> new ResourceNotFoundException("Payment not found: " + paymentId));

        payment.setStatus(PaymentStatus.REFUNDED);
        payment.setGatewayResponse("Refund processed");

        // Update order payment status
        Order order = payment.getOrder();
        order.setPaymentStatus(PaymentStatus.REFUNDED);
        orderRepository.save(order);

        return mapToResponse(paymentRepository.save(payment));
    }

    private String detectCardBrand(String cardNumber) {
        String digits = cardNumber.replaceAll("\\s+", "");
        if (digits.startsWith("4")) return "Visa";
        if (digits.startsWith("5")) return "Mastercard";
        if (digits.startsWith("3")) return "Amex";
        return "Unknown";
    }

    public PaymentResponse mapToResponse(Payment payment) {
        return PaymentResponse.builder()
                .id(payment.getId())
                .orderId(payment.getOrder() != null ? payment.getOrder().getId() : null)
                .amount(payment.getAmount())
                .method(payment.getMethod())
                .status(payment.getStatus())
                .transactionId(payment.getTransactionId())
                .cardLastFour(payment.getCardLastFour())
                .cardBrand(payment.getCardBrand())
                .createdAt(payment.getCreatedAt())
                .processedAt(payment.getProcessedAt())
                .build();
    }
}
