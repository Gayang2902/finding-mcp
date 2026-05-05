import api from './api'
import { Review, ReviewCreateRequest, PageResponse } from '@/types'

export const reviewService = {
  createReview: (data: ReviewCreateRequest) =>
    api.post<Review>('/reviews', data).then((r) => r.data),

  getProductReviews: (productId: number, params?: { page?: number; size?: number }) =>
    api.get<PageResponse<Review>>(`/reviews/product/${productId}`, { params }).then((r) => r.data),

  getMyReviews: () =>
    api.get<Review[]>('/reviews/my').then((r) => r.data),

  deleteReview: (id: number) =>
    api.delete(`/reviews/${id}`).then((r) => r.data),

  markHelpful: (id: number) =>
    api.post(`/reviews/${id}/helpful`).then((r) => r.data),

  reportReview: (id: number, reason: string) =>
    api.post(`/reviews/${id}/report`, { reason }).then((r) => r.data),
}
