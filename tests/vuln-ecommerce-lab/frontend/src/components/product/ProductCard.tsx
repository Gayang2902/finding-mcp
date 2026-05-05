import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Heart, ShoppingCart, Star } from 'lucide-react'
import { clsx } from 'clsx'
import { Product } from '../../types'
import PriceDisplay from '../common/PriceDisplay'

interface ProductCardProps {
  product: Product
  onAddToCart?: (product: Product) => void
  onToggleWishlist?: (product: Product) => void
  isWishlisted?: boolean
  onWishlist?: (id: number) => void
}

// Named export for backward compatibility with: import { ProductCard } from '...'
export function ProductCard({
  product,
  onAddToCart,
  onToggleWishlist,
  isWishlisted = false,
  onWishlist,
}: ProductCardProps) {
  const [hovered, setHovered] = useState(false)
  const navigate = useNavigate()

  const isDiscounted = product.compareAtPrice !== undefined && product.compareAtPrice > product.price
  const inStock = product.stock > 0

  function handleCardClick() {
    navigate(`/products/${product.id}`)
  }

  function handleAddToCart(e: React.MouseEvent) {
    e.stopPropagation()
    onAddToCart?.(product)
  }

  function handleWishlist(e: React.MouseEvent) {
    e.stopPropagation()
    onToggleWishlist?.(product)
    onWishlist?.(product.id)
  }

  return (
    <div
      className="group relative flex flex-col rounded-xl border border-gray-100 bg-white shadow-sm hover:shadow-md transition-shadow cursor-pointer overflow-hidden"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onClick={handleCardClick}
    >
      {/* Image */}
      <div className="relative aspect-square overflow-hidden bg-gray-50">
        {product.imageUrl ? (
          <img
            src={product.imageUrl}
            alt={product.name}
            className={clsx(
              'h-full w-full object-cover transition-transform duration-300',
              hovered && 'scale-105'
            )}
          />
        ) : (
          <div className="flex h-full w-full items-center justify-center text-gray-300">
            <ShoppingCart className="h-12 w-12" />
          </div>
        )}

        {/* Sale badge */}
        {isDiscounted && (
          <span className="absolute top-2 left-2 rounded-full bg-red-500 px-2 py-0.5 text-xs font-bold text-white">
            SALE
          </span>
        )}

        {/* Out of stock overlay */}
        {!inStock && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/40">
            <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-gray-700">
              Out of Stock
            </span>
          </div>
        )}

        {/* Wishlist button */}
        <button
          onClick={handleWishlist}
          className={clsx(
            'absolute top-2 right-2 rounded-full p-1.5 shadow transition-all',
            isWishlisted
              ? 'bg-red-500 text-white'
              : 'bg-white text-gray-400 hover:text-red-500',
            !hovered && !isWishlisted && 'opacity-0 group-hover:opacity-100'
          )}
          aria-label={isWishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
        >
          <Heart className={clsx('h-4 w-4', isWishlisted && 'fill-current')} />
        </button>

        {/* Quick add to cart */}
        {inStock && onAddToCart && (
          <button
            onClick={handleAddToCart}
            className={clsx(
              'absolute bottom-0 left-0 right-0 bg-indigo-600 py-2 text-xs font-semibold text-white',
              'flex items-center justify-center gap-1.5 transition-all duration-200',
              hovered ? 'translate-y-0 opacity-100' : 'translate-y-full opacity-0'
            )}
          >
            <ShoppingCart className="h-3.5 w-3.5" />
            Add to Cart
          </button>
        )}
      </div>

      {/* Info */}
      <div className="flex flex-col gap-1.5 p-3">
        {product.category && (
          <span className="text-xs text-indigo-500 font-medium truncate">
            {product.category.name}
          </span>
        )}

        <Link
          to={`/products/${product.id}`}
          onClick={(e) => e.stopPropagation()}
          className="text-sm font-semibold text-gray-800 line-clamp-2 hover:text-indigo-600 transition-colors leading-snug"
        >
          {product.name}
        </Link>

        {product.reviewCount > 0 && (
          <div className="flex items-center gap-1">
            <Star className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" />
            <span className="text-xs font-medium text-gray-700">{product.averageRating.toFixed(1)}</span>
            <span className="text-xs text-gray-400">({product.reviewCount})</span>
          </div>
        )}

        <PriceDisplay
          price={product.price}
          compareAtPrice={product.compareAtPrice}
          size="sm"
        />
      </div>
    </div>
  )
}

export default ProductCard
