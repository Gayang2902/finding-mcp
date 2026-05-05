import api from './api'
import { User, Review, AuditLog, DashboardStats, PageResponse, Role, ReviewStatus } from '@/types'

export const adminService = {
  getDashboard: () =>
    api.get<DashboardStats>('/admin/dashboard').then((r) => r.data),

  getUsers: (params?: { page?: number; size?: number; q?: string }) =>
    api.get<PageResponse<User>>('/admin/users', { params }).then((r) => r.data),

  updateUserRole: (id: number, role: Role) =>
    api.put<User>(`/admin/users/${id}/role`, { role }).then((r) => r.data),

  toggleUserStatus: (id: number) =>
    api.put<User>(`/admin/users/${id}/toggle`).then((r) => r.data),

  deleteUser: (id: number) =>
    api.delete(`/admin/users/${id}`).then((r) => r.data),

  getPendingReviews: (params?: { page?: number; size?: number }) =>
    api.get<PageResponse<Review>>('/admin/reviews/pending', { params }).then((r) => r.data),

  updateReviewStatus: (id: number, status: ReviewStatus) =>
    api.put<Review>(`/admin/reviews/${id}/status`, { status }).then((r) => r.data),

  getAuditLogs: (params?: { page?: number; size?: number }) =>
    api.get<PageResponse<AuditLog>>('/admin/audit-logs', { params }).then((r) => r.data),
}
