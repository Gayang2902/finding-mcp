import api from './api'
import { Coupon, CouponApplyRequest } from '@/types'

export const couponService = {
  applyCoupon: (data: CouponApplyRequest) =>
    api.post<{ discount: number; coupon: Coupon }>('/coupons/apply', data).then((r) => r.data),

  validateCoupon: (code: string) =>
    api.get<Coupon>(`/coupons/validate/${code}`).then((r) => r.data),

  createCoupon: (data: Partial<Coupon>) =>
    api.post<Coupon>('/admin/coupons', data).then((r) => r.data),

  updateCoupon: (id: number, data: Partial<Coupon>) =>
    api.put<Coupon>(`/admin/coupons/${id}`, data).then((r) => r.data),

  getActiveCoupons: () =>
    api.get<Coupon[]>('/admin/coupons').then((r) => r.data),
}
