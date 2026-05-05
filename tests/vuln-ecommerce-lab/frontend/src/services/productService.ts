import api from './api'
import { Product, PageResponse, ProductSearchParams } from '@/types'

export const productService = {
  getProducts: (params?: ProductSearchParams) =>
    api.get<PageResponse<Product>>('/products', { params }).then((r) => r.data),

  getProductById: (id: number) =>
    api.get<Product>(`/products/${id}`).then((r) => r.data),

  searchProducts: (params: ProductSearchParams) =>
    api.get<PageResponse<Product>>('/products/search', { params }).then((r) => r.data),

  getTopRated: (limit = 8) =>
    api.get<Product[]>('/products/top-rated', { params: { limit } }).then((r) => r.data),

  getFeatured: () =>
    api.get<Product[]>('/products/featured').then((r) => r.data),

  getByCategory: (categoryId: number, params?: ProductSearchParams) =>
    api.get<PageResponse<Product>>(`/products/category/${categoryId}`, { params }).then((r) => r.data),

  createProduct: (data: Partial<Product>) =>
    api.post<Product>('/products', data).then((r) => r.data),

  updateProduct: (id: number, data: Partial<Product>) =>
    api.put<Product>(`/products/${id}`, data).then((r) => r.data),

  deleteProduct: (id: number) =>
    api.delete(`/products/${id}`).then((r) => r.data),

  getCategories: () =>
    api.get<{ id: number; name: string; slug: string; imageUrl?: string }[]>('/categories').then((r) => r.data),
}
