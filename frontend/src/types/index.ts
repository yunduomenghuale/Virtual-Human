export type Role = 'admin' | 'safety_officer' | 'experimenter'
export type Skill = 'knowledge_qa' | 'report_gen' | 'hazard_detect' | 'analytics' | 'scenario_training'
export type Severity = 'low' | 'medium' | 'high'

export interface UserInfo {
  id: number
  username: string
  real_name: string
  lab_name: string
  role: Role
  role_label: string
  skills: Skill[]
}

export interface Hazard {
  name: string
  category: string
  severity: Severity
  description: string
  suggestion: string
  bbox: [number, number, number, number]
}

export interface HazardDetection {
  id: number
  user: number
  user_name: string
  lab_name: string
  original_image: string
  annotated_image: string | null
  summary: string
  overall_severity: Severity
  hazards: Hazard[]
  image_width: number
  image_height: number
  hazard_count: number
  created_at: string
}

export interface QAResult {
  id: number
  question: string
  answer: string
  sources: { title: string; snippet: string; score: number }[]
  created_at: string
}

export interface ReportSummary {
  id: number
  title: string
  lab_name: string
  inspector: string
  overall_severity: Severity
  summary_stats: { total: number; by_severity: Record<string, number>; by_category: Record<string, number> }
  creator_name: string
  detection_count: number
  pdf_file: string | null
  docx_file: string | null
  created_at: string
  updated_at: string
}

export interface ReportDetail extends ReportSummary {
  agent_evaluation: string
  references: { title: string; snippet: string }[]
  extra_notes: string
  detections: (HazardDetection & { original_image: string | null })[]
}

/* ===== Agent ===== */
export type AgentRole = 'system' | 'user' | 'assistant' | 'tool'

export interface AgentMessage {
  role: AgentRole
  content: string
  /** 仅前端用,用于渲染 */
  attachmentUrl?: string
  /** 持久化用 base64,避免 blob URL 刷新后失效 */
  attachmentBase64?: string
  toolCalls?: AgentToolCall[]
  pending?: boolean
}

export type AgentToolPayload =
  | { type: 'knowledge_qa'; query: string; answer: string;
      sources: { title: string; snippet: string; score: number }[] }
  | { type: 'hazard_detection'; data: HazardDetection }
  | { type: 'report'; data: ReportDetail }
  | { type: 'analytics'; metric: string; data: any }
  | { type: 'scenario_training'; mode: 'teaching' | 'testing'; score?: number; analysis?: string; data: any }
  | { type: 'error'; tool: string; message: string }

export interface AgentToolCall {
  name: string
  args: Record<string, any>
  skill: Skill | string
  ok: boolean
  result: AgentToolPayload
}

export interface AgentChatResponse {
  message: string
  tool_calls: AgentToolCall[]
  enabled_skills: Skill[]
}

export interface Lab {
  id: number
  name: string
  manager: number | null
  manager_name?: string
  created_at: string
  updated_at: string
}
