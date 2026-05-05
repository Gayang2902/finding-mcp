package com.vulnshop.repository;

import com.vulnshop.entity.Order;
import com.vulnshop.entity.OrderStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import java.util.List;
import java.util.Optional;

@Repository
public interface OrderRepository extends JpaRepository<Order, Long> {

    List<Order> findByUserId(Long userId);

    Optional<Order> findByOrderNumber(String orderNumber);

    List<Order> findByUserIdAndStatus(Long userId, OrderStatus status);

    List<Order> findByStatusIn(List<OrderStatus> statuses);
}
