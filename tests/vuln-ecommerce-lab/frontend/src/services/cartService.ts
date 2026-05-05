import api from './api'
import { Cart, CartItemRequest } from '@/types'

export const cartService = {
  getCart: () =>
    api.get<Cart>('/cart').then((r) => r.data),

  addItem: (data: CartItemRequest) =>
    api.post<Cart>('/cart/items', data).then((r) => r.data),

  updateItem: (itemId: number, quantity: number) =>
    api.put<Cart>(`/cart/items/${itemId}`, { quantity }).then((r) => r.data),

  removeItem: (itemId: number) =>
    api.delete<Cart>(`/cart/items/${itemId}`).then((r) => r.data),

  clearCart: () =>
    api.delete('/cart').then((r) => r.data),
}
