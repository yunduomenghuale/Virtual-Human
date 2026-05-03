import { http } from './http'
import type { HazardDetection } from '@/types'

export const hazardApi = {
  detect: (image: File, lab_id: number | null = null, other_location = '', extra_instruction = '') => {
    const fd = new FormData()
    fd.append('image', image)
    if (lab_id) fd.append('lab_id', String(lab_id))
    fd.append('other_location', other_location)
    fd.append('extra_instruction', extra_instruction)
    return http.post<unknown, HazardDetection>('/hazards/detect/', fd)
  },
  list: (params?: any) =>
    http.get<unknown, { results: HazardDetection[]; count: number }>('/hazards/', { params }),
  retrieve: (id: number) => http.get<unknown, HazardDetection>(`/hazards/${id}/`),
  remove: (id: number) => http.delete(`/hazards/${id}/`),
  labs: () => http.get<unknown, { labs: string[] }>('/hazards/labs/'),
  updateLab: (id: number, lab_name: string) =>
    http.patch<unknown, HazardDetection>(`/hazards/${id}/update_lab/`, { lab_name }),
  updateLocation: (id: number, data: { lab_id?: number | null; other_location?: string }) =>
    http.patch<unknown, HazardDetection>(`/hazards/${id}/update_location/`, data),
}
