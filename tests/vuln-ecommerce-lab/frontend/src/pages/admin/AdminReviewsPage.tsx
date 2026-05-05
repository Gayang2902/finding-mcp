import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { Star, Check, X } from 'lucide-react'
import { adminService } from '../../services/adminService'
import { ReviewStatus } from '../../types'
import { formatDate } from '../../utils/formatters'
import { ReviewStatusBadge } from '../../components/common/StatusBadge'
import StarRating from '../../components/common/StarRating'
import LoadingSpinner from '../../components/common/LoadingSpinner'
import Pagination from '../../components/common/Pagination'
import toast from 'react-hot-toast'

const STATUS_TABS = [
  { label: 'Pending', value: ReviewStatus.PENDING },
  { label: 'Approved', value: ReviewStatus.APPROVED },
  { label: 'Rejected', value: ReviewStatus.REJECTED },
]

export default function AdminReviewsPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<ReviewStatus>(ReviewStatus.PENDING)
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery(
    ['admin-reviews', statusFilter, page],
    () => adminService.getPendingReviews({ page: page - 1, size: 20 }),
    { keepPreviousData: true }
  )

  const updateStatus = useMutation(
    ({ id, status }: { id: number; status: ReviewStatus }) => adminService.updateReviewStatus(id, status),
    {
      onSuccess: (_, { status }) => {
        queryClient.invalidateQueries('admin-reviews')
        toast.success(`Review ${status === ReviewStatus.APPROVED ? 'approved' : 'rejected'}`)
      },
    }
  )

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Review Moderation</h1>

      {/* Status tabs */}
      <div className="flex gap-1 mb-6">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => { setStatusFilter(tab.value); setPage(1) }}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              statusFilter === tab.value ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="flex justify-center py-16"><LoadingSpinner size="lg" /></div>
      ) : !data?.content.length ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <Star className="w-10 h-10 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">No {statusFilter.toLowerCase()} reviews</p>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {data.content.map((review) => (
              <div key={review.id} className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <StarRating rating={review.rating} size="sm" />
                      <span className="text-sm font-semibold text-gray-900">{review.title}</span>
                      <ReviewStatusBadge status={review.status} />
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{review.body}</p>
                    <div className="flex items-center gap-3 text-xs text-gray-400">
                      <span>By: {review.user?.firstName} {review.user?.lastName} ({review.user?.email})</span>
                      <span>·</span>
                      <span>Product ID: {review.productId}</span>
                      <span>·</span>
                      <span>{formatDate(review.createdAt)}</span>
                    </div>
                  </div>
                  {statusFilter === ReviewStatus.PENDING && (
                    <div className="flex gap-2 flex-shrink-0">
                      <button
                        onClick={() => updateStatus.mutate({ id: review.id, status: ReviewStatus.APPROVED })}
                        disabled={updateStatus.isLoading}
                        className="flex items-center gap-1.5 bg-green-50 text-green-700 border border-green-200 text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-green-100 disabled:opacity-50"
                      >
                        <Check className="w-3.5 h-3.5" /> Approve
                      </button>
                      <button
                        onClick={() => updateStatus.mutate({ id: review.id, status: ReviewStatus.REJECTED })}
                        disabled={updateStatus.isLoading}
                        className="flex items-center gap-1.5 bg-red-50 text-red-700 border border-red-200 text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-red-100 disabled:opacity-50"
                      >
                        <X className="w-3.5 h-3.5" /> Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          {data.totalPages > 1 && (
            <div className="mt-6">
              <Pagination page={page} totalPages={data.totalPages} onPageChange={setPage} />
            </div>
          )}
        </>
      )}
    </div>
  )
}
