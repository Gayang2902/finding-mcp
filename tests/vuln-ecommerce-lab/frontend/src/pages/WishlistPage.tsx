import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useNavigate } from 'react-router-dom'
import { Heart, ShoppingCart, Trash2 } from 'lucide-react'
import { wishlistService } from '../services/wishlistService'
import { useCart } from '../hooks/useCart'
import { formatCurrency } from '../utils/formatters'
import LoadingSpinner from '../components/common/LoadingSpinner'
import EmptyState from '../components/common/EmptyState'
import StarRating from '../components/common/StarRating'
import toast from 'react-hot-toast'

export default function WishlistPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { addItem } = useCart()

  const { data: wishlist, isLoading } = useQuery('wishlist', wishlistService.getWishlist)

  const removeMutation = useMutation(wishlistService.removeFromWishlist, {
    onSuccess: () => {
      queryClient.invalidateQueries('wishlist')
      toast.success('Removed from wishlist')
    },
  })

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!wishlist?.length) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16">
        <EmptyState
          icon={<Heart className="w-10 h-10" />}
          title="Your wishlist is empty"
          description="Save products you love and come back to them later."
          actionLabel="Browse Products"
          onAction={() => navigate('/products')}
        />
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        My Wishlist <span className="text-gray-400 font-normal text-lg">({wishlist.length})</span>
      </h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {wishlist.map((product) => (
          <div key={product.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-sm transition-shadow">
            <div
              className="aspect-video bg-gray-100 overflow-hidden cursor-pointer"
              onClick={() => navigate(`/products/${product.id}`)}
            >
              {product.imageUrl ? (
                <img src={product.imageUrl} alt={product.name} className="w-full h-full object-cover hover:scale-105 transition-transform duration-200" />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-300">
                  <ShoppingCart className="w-10 h-10" />
                </div>
              )}
            </div>
            <div className="p-4">
              <p className="text-xs text-gray-500 mb-0.5">{product.category?.name}</p>
              <h3
                className="text-sm font-semibold text-gray-900 cursor-pointer hover:text-indigo-600 line-clamp-2 mb-2"
                onClick={() => navigate(`/products/${product.id}`)}
              >
                {product.name}
              </h3>
              <div className="flex items-center gap-1 mb-3">
                <StarRating rating={product.averageRating} size="sm" />
                <span className="text-xs text-gray-500">({product.reviewCount})</span>
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-base font-bold text-gray-900">{formatCurrency(product.price)}</span>
                  {product.compareAtPrice && (
                    <span className="text-xs text-gray-400 line-through ml-1">{formatCurrency(product.compareAtPrice)}</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => removeMutation.mutate(product.id)}
                    className="p-1.5 text-gray-400 hover:text-red-500 transition-colors"
                    title="Remove from wishlist"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => addItem({ productId: product.id, quantity: 1 })}
                    disabled={product.stock === 0}
                    className="flex items-center gap-1.5 bg-indigo-600 text-white text-xs font-medium px-3 py-1.5 rounded-lg hover:bg-indigo-700 disabled:opacity-40 transition-colors"
                  >
                    <ShoppingCart className="w-3.5 h-3.5" />
                    Add to Cart
                  </button>
                </div>
              </div>
              {product.stock === 0 && (
                <p className="text-xs text-red-500 mt-1">Out of stock</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
