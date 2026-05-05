import { useQuery } from 'react-query'
import { productService } from '@/services/productService'
import { ProductSearchParams } from '@/types'

export function useProducts(params?: ProductSearchParams) {
  return useQuery(['products', params], () => productService.getProducts(params), {
    keepPreviousData: true,
  })
}

export function useProduct(id: number) {
  return useQuery(['product', id], () => productService.getProductById(id), {
    enabled: !!id,
  })
}

export function useTopRatedProducts(limit = 8) {
  return useQuery(['products', 'top-rated', limit], () => productService.getTopRated(limit))
}

export function useCategories() {
  return useQuery('categories', () => productService.getCategories())
}

export function useProductSearch(params: ProductSearchParams) {
  return useQuery(['products', 'search', params], () => productService.searchProducts(params), {
    enabled: !!(params.q || params.categoryId),
    keepPreviousData: true,
  })
}
