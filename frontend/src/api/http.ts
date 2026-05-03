import axios from 'axios'
import { ElMessage } from 'element-plus'

export const http = axios.create({
  baseURL: '/api',
  timeout: 120000,
})

let isRefreshing = false
let refreshSubscribers: ((token: string) => void)[] = []

function onRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token))
  refreshSubscribers = []
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb)
}

async function doRefresh(): Promise<string> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) throw new Error('no refresh token')

  const resp = await fetch('/api/auth/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: refreshToken }),
  })
  if (!resp.ok) throw new Error('refresh failed')

  const data = await resp.json()
  localStorage.setItem('access_token', data.access)
  return data.access
}

http.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

http.interceptors.response.use(
  resp => resp.data,
  async error => {
    const originalRequest = error.config
    const status = error.response?.status

    if (status === 401 && originalRequest && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise(resolve => {
          addRefreshSubscriber(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(http(originalRequest))
          })
        })
      }

      isRefreshing = true
      originalRequest._retry = true

      try {
        const newToken = await doRefresh()
        onRefreshed(newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return http(originalRequest)
      } catch {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        const path = window.location.pathname
        if (path !== '/login') {
          ElMessage.warning('登录已失效,请重新登录')
          window.location.href = '/login'
        }
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    if (status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      const path = window.location.pathname
      if (path !== '/login') {
        ElMessage.warning('登录已失效,请重新登录')
        window.location.href = '/login'
      }
    } else {
      const detail = error.response?.data?.detail
        || error.response?.data?.non_field_errors?.[0]
        || error.message
        || '请求失败'
      ElMessage.error(typeof detail === 'string' ? detail : JSON.stringify(detail))
    }
    return Promise.reject(error)
  },
)
