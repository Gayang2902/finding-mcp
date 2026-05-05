import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ShoppingCart, Heart, Star, Truck, ArrowLeft, Minus, Plus, User } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useProduct } from '../hooks/useProducts'
import { useCart } from '../hooks/useCart'
import { useAuth } from '../context/AuthContext'
import { reviewService } from '../services/reviewService'
import { wishlistService } from '../services/wishlistService'
import { formatCurrency, formatDate } from '../utils/formatters'
import LoadingSpinner from '../components/common/LoadingSpinner'
import StarRating from '../components/common/StarRating'
import { ProductCard } from '../components/product/ProductCard'
import { useProducts } from '../hooks/useProducts'
import toast from 'react-hot-toast'

export default function ProductDetailPage() {
  const { id } = useParams<{ id: string }>()
  const productId = Number(id)
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()
  const { addItem, isAddingItem } = useCart()
  const queryClient = useQueryClient()

  const [quantity, setQuantity] = useState(1)
  const [reviewRating, setReviewRating] = useState(0)
  const [reviewTitle, setReviewTitle] = useState('')
  const [reviewBody, setReviewBody] = useState('')

  const { data: product, isLoading } = useProduct(productId)
  const { data: reviewsData } = useQuery(
    ['reviews', productId],
    () => reviewService.getProductReviews(productId),
    { enabled: !!productId }
  )
  const { data: relatedData } = useProducts({ categoryId: product?.categoryId, size: 4 })
  const related = relatedData?.content.filter((p) => p.id !== productId).slice(0, 4)

  const addReview = useMutation(
    () => reviewService.createReview({ productId, rating: reviewRating, title: reviewTitle, body: reviewBody }),
    {
      onSuccess: () => {
        toast.success('Review submitted for moderation')
        setReviewRating(0)
        setReviewTitle('')
        setReviewBody('')
        queryClient.invalidateQueries(['reviews', productId])
      },
    }
  )

  const addWishlist = useMutation(
    () => wishlistService.addToWishlist(productId),
    { onSuccess: () => { toast.success('Added to wishlist') } }
  )

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!product) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center">
        <p className="text-gray-500">Product not found.</p>
        <Link to="/products" className="text-indigo-600 mt-4 inline-block">Back to Products</Link>
      </div>
    )
  }

  const inStock = product.stock > 0
  const discount = product.compareAtPrice
    ? Math.round((1 - product.price / product.compareAtPrice) * 100)
    : 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-1 text-gray-500 hover:text-gray-700 text-sm mb-6"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 mb-12">
        {/* Image */}
        <div>
          <div className="aspect-square bg-gray-100 rounded-2xl overflow-hidden">
            {product.imageUrl ? (
              <img src={product.imageUrl} alt={product.name} className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-300">
                <ShoppingCart className="w-20 h-20" />
              </div>
            )}
          </div>
          {product.images && product.images.length > 1 && (
            <div className="flex gap-2 mt-3">
              {product.images.slice(0, 5).map((img, i) => (
                <img key={i} src={img} alt="" className="w-16 h-16 rounded-lg object-cover border-2 border-transparent hover:border-indigo-400 cursor-pointer" />
              ))}
            </div>
          )}
        </div>

        {/* Info */}
        <div>
          {product.category && (
            <p className="text-xs text-indigo-600 font-medium uppercase tracking-wider mb-1">{product.category.name}</p>
          )}
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{product.name}</h1>

          <div className="flex items-center gap-3 mb-4">
            <StarRating rating={product.averageRating} showValue />
            <span className="text-sm text-gray-500">({product.reviewCount} reviews)</span>
          </div>

          <div className="flex items-baseline gap-3 mb-4">
            <span className="text-3xl font-extrabold text-gray-900">{formatCurrency(product.price)}</span>
            {product.compareAtPrice && (
              <>
                <span className="text-lg text-gray-400 line-through">{formatCurrency(product.compareAtPrice)}</span>
                <span className="text-sm font-semibold text-red-500 bg-red-50 px-2 py-0.5 rounded">-{discount}%</span>
              </>
            )}
          </div>

          <div className={`inline-flex items-center gap-1.5 text-sm font-medium mb-4 px-3 py-1 rounded-full ${inStock ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
            <span className={`w-2 h-2 rounded-full ${inStock ? 'bg-green-500' : 'bg-red-400'}`} />
            {inStock ? `In Stock (${product.stock} available)` : 'Out of Stock'}
          </div>

          <p className="text-gray-600 text-sm leading-relaxed mb-6">{product.description}</p>

          {/* Quantity */}
          {inStock && (
            <div className="flex items-center gap-3 mb-5">
              <span className="text-sm font-medium text-gray-700">Qty:</span>
              <div className="flex items-center border border-gray-300 rounded-lg">
                <button
                  onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  className="px-3 py-2 text-gray-500 hover:text-gray-700"
                >
                  <Minus className="w-4 h-4" />
                </button>
                <span className="w-10 text-center text-sm font-medium">{quantity}</span>
                <button
                  onClick={() => setQuantity((q) => Math.min(product.stock, q + 1))}
                  className="px-3 py-2 text-gray-500 hover:text-gray-700"
                >
                  <Plus className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => addItem({ productId: product.id, quantity })}
              disabled={!inStock || isAddingItem}
              className="flex-1 flex items-center justify-center gap-2 bg-indigo-600 text-white font-semibold py-3 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50"
            >
              <ShoppingCart className="w-5 h-5" />
              {isAddingItem ? 'Adding…' : 'Add to Cart'}
            </button>
            <button
              onClick={() => {
                if (!isAuthenticated) { navigate('/login'); return }
                addWishlist.mutate()
              }}
              className="p-3 border-2 border-gray-200 rounded-xl text-gray-500 hover:border-red-300 hover:text-red-500 transition-colors"
            >
              <Heart className="w-5 h-5" />
            </button>
          </div>

          {/* Shipping info */}
          <div className="flex items-center gap-2 mt-5 text-sm text-gray-500 bg-gray-50 rounded-lg px-3 py-2">
            <Truck className="w-4 h-4 flex-shrink-0" />
            Free shipping on orders over $50
          </div>

          {/* Seller */}
          {product.seller && (
            <div className="mt-4 flex items-center gap-2 text-sm text-gray-500">
              <User className="w-4 h-4" />
              Sold by <span className="font-medium text-gray-700">{product.seller.firstName} {product.seller.lastName}</span>
            </div>
          )}
        </div>
      </div>

      {/* Reviews */}
      <div className="mb-12">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Customer Reviews</h2>

        {/* Average rating summary */}
        <div className="bg-gray-50 rounded-xl p-6 flex items-center gap-8 mb-6">
          <div className="text-center">
            <p className="text-5xl font-extrabold text-gray-900">{product.averageRating.toFixed(1)}</p>
            <StarRating rating={product.averageRating} size="sm" />
            <p className="text-xs text-gray-500 mt-1">{product.reviewCount} reviews</p>
          </div>
        </div>

        {/* Review list */}
        <div className="space-y-4 mb-8">
          {reviewsData?.content.map((review) => (
            <div key={review.id} className="bg-white border border-gray-200 rounded-xl p-5">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <StarRating rating={review.rating} size="sm" />
                    <span className="text-sm font-semibold text-gray-900">{review.title}</span>
                  </div>
                  <p className="text-xs text-gray-500">
                    {review.user?.firstName} {review.user?.lastName} · {formatDate(review.createdAt)}
                  </p>
                </div>
              </div>
              <p className="text-sm text-gray-700">{review.body}</p>
            </div>
          ))}
          {!reviewsData?.content.length && (
            <p className="text-sm text-gray-500 text-center py-6">No reviews yet. Be the first to review!</p>
          )}
        </div>

        {/* Write review */}
        {isAuthenticated && (
          <div className="bg-white border border-gray-200 rounded-xl p-6">
            <h3 className="text-base font-semibold text-gray-900 mb-4">Write a Review</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rating</label>
                <StarRating rating={reviewRating} interactive onChange={setReviewRating} size="lg" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Title</label>
                <input
                  type="text"
                  value={reviewTitle}
                  onChange={(e) => setReviewTitle(e.target.value)}
                  placeholder="Summarize your review"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Review</label>
                <textarea
                  value={reviewBody}
                  onChange={(e) => setReviewBody(e.target.value)}
                  rows={4}
                  placeholder="Share your experience with this product"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                />
              </div>
              <button
                onClick={() => addReview.mutate()}
                disabled={!reviewRating || !reviewTitle || !reviewBody || addReview.isLoading}
                className="bg-indigo-600 text-white font-medium px-5 py-2.5 rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {addReview.isLoading ? 'Submitting…' : 'Submit Review'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Related products */}
      {related && related.length > 0 && (
        <div>
          <h2 className="text-xl font-bold text-gray-900 mb-6">Related Products</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {related.map((p) => (
              <ProductCard key={p.id} product={p} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
