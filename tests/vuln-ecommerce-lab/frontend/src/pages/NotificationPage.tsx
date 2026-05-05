import { useQuery, useMutation, useQueryClient } from 'react-query'
import { useNavigate } from 'react-router-dom'
import { Bell, Package, CreditCard, Truck, Tag, Star, Info, CheckCheck } from 'lucide-react'
import { notificationService } from '../services/notificationService'
import { NotificationType } from '../types'
import { formatDateTime } from '../utils/formatters'
import LoadingSpinner from '../components/common/LoadingSpinner'
import EmptyState from '../components/common/EmptyState'
import toast from 'react-hot-toast'

const TYPE_ICONS: Record<NotificationType, React.ReactNode> = {
  [NotificationType.ORDER_UPDATE]: <Package className="w-4 h-4" />,
  [NotificationType.PAYMENT]: <CreditCard className="w-4 h-4" />,
  [NotificationType.SHIPPING]: <Truck className="w-4 h-4" />,
  [NotificationType.PROMOTION]: <Tag className="w-4 h-4" />,
  [NotificationType.REVIEW]: <Star className="w-4 h-4" />,
  [NotificationType.SYSTEM]: <Info className="w-4 h-4" />,
}

const TYPE_COLORS: Record<NotificationType, string> = {
  [NotificationType.ORDER_UPDATE]: 'bg-blue-100 text-blue-600',
  [NotificationType.PAYMENT]: 'bg-green-100 text-green-600',
  [NotificationType.SHIPPING]: 'bg-purple-100 text-purple-600',
  [NotificationType.PROMOTION]: 'bg-orange-100 text-orange-600',
  [NotificationType.REVIEW]: 'bg-yellow-100 text-yellow-600',
  [NotificationType.SYSTEM]: 'bg-gray-100 text-gray-600',
}

export default function NotificationPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data: notifications, isLoading } = useQuery('notifications', notificationService.getNotifications)

  const markRead = useMutation(notificationService.markAsRead, {
    onSuccess: () => queryClient.invalidateQueries('notifications'),
  })

  const markAllRead = useMutation(notificationService.markAllAsRead, {
    onSuccess: () => {
      queryClient.invalidateQueries('notifications')
      toast.success('All notifications marked as read')
    },
  })

  const unreadCount = notifications?.filter((n) => !n.isRead).length ?? 0

  const handleClick = (notification: typeof notifications extends (infer T)[] | undefined ? T : never) => {
    if (!notification) return
    if (!notification.isRead) markRead.mutate(notification.id)
    if (notification.resourceType === 'ORDER' && notification.resourceId) {
      navigate(`/orders/${notification.resourceId}`)
    }
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Notifications</h1>
          {unreadCount > 0 && (
            <span className="bg-indigo-600 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {unreadCount}
            </span>
          )}
        </div>
        {unreadCount > 0 && (
          <button
            onClick={() => markAllRead.mutate()}
            disabled={markAllRead.isLoading}
            className="flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-700 font-medium"
          >
            <CheckCheck className="w-4 h-4" />
            Mark all read
          </button>
        )}
      </div>

      {!notifications?.length ? (
        <EmptyState
          icon={<Bell className="w-10 h-10" />}
          title="No notifications"
          description="You're all caught up! Notifications will appear here."
        />
      ) : (
        <div className="space-y-2">
          {notifications.map((notification) => (
            <div
              key={notification.id}
              onClick={() => handleClick(notification)}
              className={`flex gap-4 p-4 rounded-xl border cursor-pointer transition-all ${
                notification.isRead
                  ? 'bg-white border-gray-100 hover:border-gray-200'
                  : 'bg-indigo-50 border-indigo-100 hover:border-indigo-200'
              }`}
            >
              <div className={`w-9 h-9 rounded-full flex items-center justify-center flex-shrink-0 ${TYPE_COLORS[notification.type]}`}>
                {TYPE_ICONS[notification.type]}
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p className={`text-sm font-medium ${notification.isRead ? 'text-gray-700' : 'text-gray-900'}`}>
                    {notification.title}
                  </p>
                  {!notification.isRead && (
                    <span className="w-2 h-2 bg-indigo-600 rounded-full flex-shrink-0 mt-1.5" />
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-0.5">{notification.message}</p>
                <p className="text-xs text-gray-400 mt-1">{formatDateTime(notification.createdAt)}</p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
