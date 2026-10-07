import request from '../request'

export interface UpdateCheckResult {
  current_version: string
  has_update: boolean
  latest_version?: string | null
  notes?: string | null
  release_url?: string | null
}

export interface UpdateStatus {
  phase: 'idle' | 'checking' | 'downloading' | 'verifying' | 'installing' | 'ready' | 'done' | 'error'
  percent: number
  bytes_done: number
  bytes_total: number
  message: string
  error?: string | null
}

export const updateApi = {
  check: (): Promise<UpdateCheckResult> => {
    return request.get('/update/check').then(res => res.data)
  },
  status: (): Promise<UpdateStatus> => {
    return request.get('/update/status').then(res => res.data)
  },
  apply: (): Promise<{ task_started: boolean; message: string }> => {
    return request.post('/update/apply').then(res => res.data)
  },
  restart: (): Promise<{ message: string }> => {
    return request.post('/update/restart').then(res => res.data)
  }
}