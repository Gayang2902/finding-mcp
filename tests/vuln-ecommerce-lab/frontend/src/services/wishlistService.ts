import api from './api'
import { Product } from '@/types'

export const wishlistService = {
  getWishlist: () =>
    api.get<Product[]>('/wishlist').then((r) => r.data),

  addToWishlist: (productId: number) =>
    api.post('/wishlist', { productId }).then((r) => r.data),

  removeFromWishlist: (productId: number) =>
    api.delete(`/wishlist/${productId}`).then((r) => r.data),
}
