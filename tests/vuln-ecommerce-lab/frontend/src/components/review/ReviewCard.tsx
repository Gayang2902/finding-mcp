import { useState } from 'react'
import { format } from 'date-fns'
import { ThumbsUp, Flag, BadgeCheck } from 'lucide-react'
import { Review } from '../../types'
import StarRating from '../common/StarRating'

interface ReviewCardProps {
  review: Review
  onHelpful?: (reviewId: number) => void
  onReport?: (reviewId: number) => void
}

export default function ReviewCard({ review, onHelpful, onReport }: ReviewCardProps) {
  const [markedHelpful, setMarkedHelpful] = useState(false)

  function handleHelpful() {
    if (markedHelpful) return
    setMarkedHelpful(true)
    onHelpful?.(review.id)
  }

  const authorName = review.user
    ? `${review.user.firstName} ${review.user.lastName.charAt(0)}.`
    : 'Anonymous'

  return (
    <div className="rounded-xl border border-gray-100 bg-white p-5 shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-gray-900">{authorName}</span>
            <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
              <BadgeCheck className="h-3.5 w-3.5" />
              Verified Purchase
            </span>
          </div>
          <p className="text-xs text-gray-400 mt-0.5">
            {format(new Date(review.createdAt), 'MMM d, yyyy')}
          </p>
        </div>
        <StarRating rating={review.rating} size="sm" />
      </div>

      {/* Content */}
      <h4 className="text-sm font-semibold text-gray-800 mb-1">{review.title}</h4>
      <p className="text-sm text-gray-600 leading-relaxed">{review.body}</p>

      {/* Footer */}
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-gray-100">
        <div className="flex items-center gap-1.5 text-xs text-gray-500">
          <span>Was this helpful?</span>
          <button
            onClick={handleHelpful}
            disabled={markedHelpful}
            className="flex items-center gap-1 rounded-full border border-gray-200 px-2.5 py-1 hover:bg-gray-50 disabled:opacity-60 disabled:cursor-default transition-colors"
          >
            <ThumbsUp className="h-3.5 w-3.5" />
            <span>{review.helpfulCount + (markedHelpful ? 1 : 0)}</span>
          </button>
        </div>
        <button
          onClick={() => onReport?.(review.id)}
          className="flex items-center gap-1 text-xs text-gray-400 hover:text-red-500 transition-colors"
        >
          <Flag className="h-3.5 w-3.5" />
          Report
        </button>
      </div>
    </div>
  )
}
