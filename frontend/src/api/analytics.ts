import { http } from './http'

export const analyticsApi = {
  dashboard: () => http.get<unknown, any>('/analytics/dashboard/'),
  labs: () => http.get<unknown, { results: any[] }>('/analytics/labs/'),
}

export const skillPermissionApi = {
  matrix: () => http.get<unknown, any>('/skill-permissions/matrix/'),
  list: () => http.get<unknown, { results: any[] }>('/skill-permissions/'),
  update: (id: number, enabled: boolean) =>
    http.patch(`/skill-permissions/${id}/`, { enabled }),
  reset: () => http.post('/skill-permissions/reset_defaults/'),
}
