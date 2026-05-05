import api from './api'
import { Order, OrderCreateRequest, PageResponse, OrderStatus, ShippingInfo } from '@/types'

export const orderService = {
  createOrder: (data: OrderCreateRequest) =>
    api.post<Order>('/orders', data).then((r) => r.data),

  getMyOrders: (params?: { status?: OrderStatus; page?: number; size?: number }) =>
    api.get<PageResponse<Order>>('/orders/my', { params }).then((r) => r.data),

  getOrderById: (id: number) =>
    api.get<Order>(`/orders/${id}`).then((r) => r.data),

  getOrderByNumber: (orderNumber: string) =>
    api.get<Order>(`/orders/number/${orderNumber}`).then((r) => r.data),

  cancelOrder: (id: number) =>
    api.post<Order>(`/orders/${id}/cancel`).then((r) => r.data),

  getOrderTracking: (id: number) =>
    api.get<ShippingInfo>(`/orders/${id}/tracking`).then((r) => r.data),

  requestRefund: (id: number, reason: string) =>
    api.post<Order>(`/orders/${id}/refund`, { reason }).then((r) => r.data),

  getAllOrders: (params?: { status?: OrderStatus; page?: number; size?: number }) =>
    api.get<PageResponse<Order>>('/admin/orders', { params }).then((r) => r.data),

  updateOrderStatus: (id: number, status: OrderStatus, trackingNumber?: string) =>
    api.put<Order>(`/admin/orders/${id}/status`, { status, trackingNumber }).then((r) => r.data),
}
