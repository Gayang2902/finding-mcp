import api from './api'
import { Notification } from '@/types'

export const notificationService = {
  getNotifications: () =>
    api.get<Notification[]>('/notifications').then((r) => r.data),

  markAsRead: (id: number) =>
    api.post(`/notifications/${id}/read`).then((r) => r.data),

  markAllAsRead: () =>
    api.post('/notifications/read-all').then((r) => r.data),

  getUnreadCount: () =>
    api.get<{ count: number }>('/notifications/unread-count').then((r) => r.data),
}
