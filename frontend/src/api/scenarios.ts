import { http } from './http'

export interface FireScenario {
  id: number
  title: string
  topic: string
  difficulty: string
  description: string
  image: string | null
  correct_actions: string
  analysis: string
  created_at: string
  updated_at: string
  teaching_content?: string
}

export interface TrainingMaterial {
  id: number
  file: string
  file_name: string
  file_type: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message: string | null
  result_teaching: string | null
  result_scenarios: any[] | null
  created_at: string
}

export const scenarioApi = {
  // Scenarios
  list(params?: { topic?: string; difficulty?: string; page?: number; page_size?: number }) {
    return http.get('/scenarios/', { params })
  },
  
  create(data: FormData) {
    return http.post('/scenarios/', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  update(id: number, data: FormData) {
    return http.patch(`/scenarios/${id}/`, data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  delete(id: number) {
    return http.delete(`/scenarios/${id}/`)
  },

  // Materials
  uploadMaterial(data: FormData) {
    return http.post('/scenarios/materials/', data, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  processMaterial(id: number) {
    return http.post(`/scenarios/materials/${id}/process/`)
  },

  confirmImport(id: number, data: { teaching_content: string; scenarios: any[] }) {
    return http.post(`/scenarios/materials/${id}/confirm_import/`, data)
  },

  listMaterials(params?: { page?: number; page_size?: number }) {
    return http.get('/scenarios/materials/', { params })
  },

  deleteMaterial(id: number) {
    return http.delete(`/scenarios/materials/${id}/`)
  },

  evaluate(id: number, answer: string) {
    return http.post(`/scenarios/${id}/evaluate/`, { answer })
  }
}
