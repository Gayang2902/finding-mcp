import { useState } from 'react'
import { Star } from 'lucide-react'
import { Review } from '../../types'
import ReviewCard from './ReviewCard'
import Button from '../common/Button'
import EmptyState from '../common/EmptyState'

interface ReviewListProps {
  reviews: Review[]
  totalCount?: number
  averageRating?: number
  onLoadMore?: () => void
  hasMore?: boolean
  loading?: boolean
  onHelpful?: (reviewId: number) => void
  onReport?: (reviewId: number) => void
}

type SortKey = 'newest' | 'highest' | 'helpful'

const sortOptions: { value: SortKey; label: string }[] = [
  { value: 'newest', label: 'Newest' },
  { value: 'highest', label: 'Highest Rated' },
  { value: 'helpful', label: 'Most Helpful' },
]

function RatingBar({ stars, count, total }: { stars: number; count: number; total: number }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-4 text-right text-gray-500">{stars}</span>
      <Star className="h-3 w-3 fill-yellow-400 text-yellow-400 flex-shrink-0" />
      <div className="flex-1 h-2 rounded-full bg-gray-100 overflow-hidden">
        <div className="h-full rounded-full bg-yellow-400 transition-all" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-7 text-right text-gray-400">{pct}%</span>
    </div>
  )
}

export default function ReviewList({
  reviews,
  totalCount,
  averageRating,
  onLoadMore,
  hasMore = false,
  loading = false,
  onHelpful,
  onReport,
}: ReviewListProps) {
  const [sortBy, setSortBy] = useState<SortKey>('newest')

  const ratingBuckets = [5, 4, 3, 2, 1].map((stars) => ({
    stars,
    count: reviews.filter((r) => Math.round(r.rating) === stars).length,
  }))

  const sortedReviews = [...reviews].sort((a, b) => {
    if (sortBy === 'newest') return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    if (sortBy === 'highest') return b.rating - a.rating
    return b.helpfulCount - a.helpfulCount
  })

  return (
    <div className="space-y-6">
      {/* Summary */}
      {averageRating !== undefined && (
        <div className="flex flex-col sm:flex-row gap-6 rounded-xl border border-gray-100 bg-white p-6 shadow-sm">
          <div className="flex flex-col items-center justify-center flex-shrink-0">
            <span className="text-5xl font-bold text-gray-900">{averageRating.toFixed(1)}</span>
            <div className="flex gap-0.5 mt-1">
              {[1, 2, 3, 4, 5].map((s) => (
                <Star
                  key={s}
                  className={`h-4 w-4 ${s <= Math.round(averageRating) ? 'fill-yellow-400 text-yellow-400' : 'fill-gray-200 text-gray-200'}`}
                />
              ))}
            </div>
            <span className="text-sm text-gray-500 mt-1">{totalCount ?? reviews.length} reviews</span>
          </div>
          <div className="flex-1 space-y-1.5">
            {ratingBuckets.map(({ stars, count }) => (
              <RatingBar key={stars} stars={stars} count={count} total={reviews.length} />
            ))}
          </div>
        </div>
      )}

      {/* Sort */}
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500 font-medium">Sort by:</span>
        <div className="flex gap-2">
          {sortOptions.map((opt) => (
            <button
              key={opt.value}
              onClick={() => setSortBy(opt.value)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                sortBy === opt.value
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Review cards */}
      {sortedReviews.length === 0 ? (
        <EmptyState
          icon={<Star className="h-8 w-8" />}
          title="No reviews yet"
          description="Be the first to review this product."
        />
      ) : (
        <div className="space-y-4">
          {sortedReviews.map((review) => (
            <ReviewCard key={review.id} review={review} onHelpful={onHelpful} onReport={onReport} />
          ))}
        </div>
      )}

      {/* Load more */}
      {hasMore && (
        <div className="flex justify-center">
          <Button variant="outline" onClick={onLoadMore} loading={loading}>
            Load More Reviews
          </Button>
        </div>
      )}
    </div>
  )
}
