import request from '../request'

export interface HealthResult {
  status: string
  version: string
  platform: string
  python_version: string
}

export const healthApi = {
  check: (): Promise<HealthResult> => {
    return request.get('/health').then(res => res.data)
  }
}