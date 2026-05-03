import { http } from './http'
import type { Lab } from '@/types'

export interface LabListResponse {
  results: Lab[]
  count: number
}

export const labApi = {
  list: (params?: any) =>
    http.get<unknown, LabListResponse>('/labs/', { params }),
  create: (data: Partial<Lab>) =>
    http.post<unknown, Lab>('/labs/', data),
  update: (id: number, data: Partial<Lab>) =>
    http.patch<unknown, Lab>(`/labs/${id}/`, data),
  remove: (id: number) =>
    http.delete(`/labs/${id}/`),
}
