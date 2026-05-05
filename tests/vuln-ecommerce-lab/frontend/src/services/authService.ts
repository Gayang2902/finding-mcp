import api from './api'
import { AuthResponse, LoginRequest, RegisterRequest, User } from '@/types'

export const authService = {
  login: (data: LoginRequest) =>
    api.post<AuthResponse>('/auth/login', data).then((r) => r.data),

  register: (data: RegisterRequest) =>
    api.post<AuthResponse>('/auth/register', data).then((r) => r.data),

  getProfile: () =>
    api.get<User>('/auth/me').then((r) => r.data),

  refreshToken: () =>
    api.post<AuthResponse>('/auth/refresh').then((r) => r.data),

  logout: () =>
    api.post('/auth/logout').catch(() => {}),
}
