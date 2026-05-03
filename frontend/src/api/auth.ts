import { http } from './http'
import type { UserInfo } from '@/types'

export interface LoginResp {
  access: string
  refresh: string
  user: UserInfo
}

export const authApi = {
  login: (username: string, password: string) =>
    http.post<unknown, LoginResp>('/auth/login/', { username, password }),
  me: () => http.get<unknown, UserInfo>('/users/me/'),
  changePassword: (old_password: string, new_password: string) =>
    http.post('/users/change_password/', { old_password, new_password }),
}

export const userApi = {
  list: (params?: any) => http.get<unknown, { results: any[]; count: number }>('/users/', { params }),
  create: (data: any) => http.post('/users/', data),
  update: (id: number, data: any) => http.patch(`/users/${id}/`, data),
  remove: (id: number) => http.delete(`/users/${id}/`),
}
