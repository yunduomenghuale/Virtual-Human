import { http } from './http'

export const analyticsApi = {
  dashboard: () => http.get<unknown, any>('/analytics/dashboard/'),
  labs: () => http.get<unknown, { results: any[] }>('/analytics/labs/'),
  rootCause: (lab_name: string, days: number) =>
    http.post<unknown, any>('/analytics/root-cause/', { lab_name, days }),
  prediction: (lab_name: string, days: number, forecast_days: number) =>
    http.post<unknown, any>('/analytics/prediction/', { lab_name, days, forecast_days }),
}

export const skillPermissionApi = {
  matrix: () => http.get<unknown, any>('/skill-permissions/matrix/'),
  list: () => http.get<unknown, { results: any[] }>('/skill-permissions/'),
  update: (id: number, enabled: boolean) =>
    http.patch(`/skill-permissions/${id}/`, { enabled }),
  reset: () => http.post('/skill-permissions/reset_defaults/'),
}
