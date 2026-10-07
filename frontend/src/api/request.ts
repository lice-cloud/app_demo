import axios from 'axios'

// 开发期使用 VITE_API_BASE，生产期使用相对路径（同源）
const baseURL = import.meta.env.VITE_API_BASE || '/api/v1'

const request = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

request.interceptors.response.use(
  response => response,
  error => {
    console.error('[API Error]', error)
    return Promise.reject(error)
  }
)

export default request