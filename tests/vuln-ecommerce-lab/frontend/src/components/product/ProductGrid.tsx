import { Product } from '../../types'
import ProductCard from './ProductCard'
import Skeleton from '../common/Skeleton'
import EmptyState from '../common/EmptyState'
import { ShoppingBag } from 'lucide-react'

interface ProductGridProps {
  products: Product[]
  loading?: boolean
  skeletonCount?: number
  onAddToCart?: (product: Product) => void
  onToggleWishlist?: (product: Product) => void
  wishlistedIds?: number[]
}

export default function ProductGrid({
  products,
  loading = false,
  skeletonCount = 8,
  onAddToCart,
  onToggleWishlist,
  wishlistedIds = [],
}: ProductGridProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: skeletonCount }, (_, i) => (
          <Skeleton key={i} variant="card" />
        ))}
      </div>
    )
  }

  if (products.length === 0) {
    return (
      <EmptyState
        icon={<ShoppingBag className="h-10 w-10" />}
        title="No products found"
        description="Try adjusting your search or filters to find what you're looking for."
      />
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {products.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          onAddToCart={onAddToCart}
          onToggleWishlist={onToggleWishlist}
          isWishlisted={wishlistedIds.includes(product.id)}
        />
      ))}
    </div>
  )
}
