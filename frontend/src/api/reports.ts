import { http } from './http'
import type { ReportSummary, ReportDetail } from '@/types'

export const reportApi = {
  list: (params?: any) =>
    http.get<unknown, { results: ReportSummary[]; count: number }>('/reports/', { params }),
  retrieve: (id: number) => http.get<unknown, ReportDetail>(`/reports/${id}/`),
  generate: (data: {
    title: string; inspector: string; detection_ids: number[];
    lab_name?: string; lab_id?: number | null; other_location?: string;
    address?: string; extra_notes?: string;
  }) => http.post<unknown, ReportDetail>('/reports/generate/', data),
  regenerate: (id: number) => http.post<unknown, ReportDetail>(`/reports/${id}/regenerate/`),
  remove: (id: number) => http.delete(`/reports/${id}/`),
  trend: (lab_name: string) =>
    http.get<unknown, { lab_name: string; points: any[] }>('/reports/trend/', { params: { lab_name } }),
  labs: () => http.get<unknown, { labs: string[] }>('/reports/labs/'),
}
