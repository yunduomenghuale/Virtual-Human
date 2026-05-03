import type { Severity } from '@/types'

export function severityLabel(s?: Severity | string) {
  if (s === 'high') return '高'
  if (s === 'low') return '低'
  return '中'
}

export function severityTag(s?: Severity | string): 'success' | 'warning' | 'danger' | 'info' {
  if (s === 'high') return 'danger'
  if (s === 'low') return 'success'
  if (s === 'medium') return 'warning'
  return 'info'
}

export function severityColor(s?: Severity | string) {
  if (s === 'high') return '#f56c6c'
  if (s === 'low') return '#67c23a'
  return '#e6a23c'
}
