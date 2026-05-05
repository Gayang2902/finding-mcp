import api from './api'
import { Payment, PaymentRequest } from '@/types'

export const paymentService = {
  processPayment: (data: PaymentRequest) =>
    api.post<Payment>('/payments', data).then((r) => r.data),

  getPayment: (id: number) =>
    api.get<Payment>(`/payments/${id}`).then((r) => r.data),

  getMyPayments: () =>
    api.get<Payment[]>('/payments/my').then((r) => r.data),

  refundPayment: (id: number) =>
    api.post<Payment>(`/payments/${id}/refund`).then((r) => r.data),
}
