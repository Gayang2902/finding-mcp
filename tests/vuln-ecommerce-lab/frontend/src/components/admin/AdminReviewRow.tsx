import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { CheckCircle, XCircle } from 'lucide-react'
import { Review, ReviewStatus } from '../../types'
import StarRating from '../common/StarRating'
import { ReviewStatusBadge } from '../common/StatusBadge'
import Button from '../common/Button'

interface AdminReviewRowProps {
  review: Review
  onApprove?: (reviewId: number) => void
  onReject?: (reviewId: number) => void
}

export default function AdminReviewRow({ review, onApprove, onReject }: AdminReviewRowProps) {
  const isPending = review.status === ReviewStatus.PENDING

  return (
    <tr className="hover:bg-gray-50 transition-colors">
      {/* Review content */}
      <td className="px-4 py-3 max-w-xs">
        <p className="text-sm font-semibold text-gray-800 truncate">{review.title}</p>
        <p className="text-xs text-gray-500 line-clamp-2 mt-0.5">{review.body}</p>
      </td>

      {/* Product */}
      <td className="px-4 py-3">
        {review.product ? (
          <Link
            to={`/products/${review.productId}`}
            className="text-xs text-indigo-600 hover:text-indigo-700 transition-colors line-clamp-1 max-w-[140px] block"
          >
            {review.product.name}
          </Link>
        ) : (
          <span className="text-xs text-gray-400">Product #{review.productId}</span>
        )}
      </td>

      {/* User */}
      <td className="px-4 py-3">
        {review.user ? (
          <div>
            <p className="text-xs font-medium text-gray-700">
              {review.user.firstName} {review.user.lastName}
            </p>
            <p className="text-xs text-gray-400 truncate max-w-[140px]">{review.user.email}</p>
          </div>
        ) : (
          <span className="text-xs text-gray-400">User #{review.userId}</span>
        )}
      </td>

      {/* Rating + date */}
      <td className="px-4 py-3">
        <StarRating rating={review.rating} size="sm" showValue />
        <p className="text-xs text-gray-400 mt-1">{format(new Date(review.createdAt), 'MMM d, yyyy')}</p>
      </td>

      {/* Status */}
      <td className="px-4 py-3">
        <ReviewStatusBadge status={review.status} />
      </td>

      {/* Actions */}
      <td className="px-4 py-3">
        {isPending ? (
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onApprove?.(review.id)}
              className="text-green-600 hover:bg-green-50"
              iconLeft={<CheckCircle className="h-3.5 w-3.5" />}
            >
              Approve
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onReject?.(review.id)}
              className="text-red-500 hover:bg-red-50"
              iconLeft={<XCircle className="h-3.5 w-3.5" />}
            >
              Reject
            </Button>
          </div>
        ) : (
          <span className="text-xs text-gray-400">—</span>
        )}
      </td>
    </tr>
  )
}
