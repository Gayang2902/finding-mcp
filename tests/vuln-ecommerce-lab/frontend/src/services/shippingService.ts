import api from './api'
import { ShippingInfo } from '@/types'

export const shippingService = {
  getShippingByOrder: (orderId: number) =>
    api.get<ShippingInfo>(`/shipping/order/${orderId}`).then((r) => r.data),

  trackByNumber: (trackingNumber: string) =>
    api.get<ShippingInfo>(`/shipping/track/${trackingNumber}`).then((r) => r.data),
}
