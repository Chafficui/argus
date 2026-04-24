import axios from 'axios'
import keycloak from '../auth/keycloak'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
})

api.interceptors.request.use(async (config) => {
  try {
    await keycloak.updateToken(30)
  } catch {
    // Token refresh failed — redirect to login
    keycloak.login()
    return config
  }

  if (keycloak.token) {
    config.headers.Authorization = `Bearer ${keycloak.token}`
  }
  return config
})

export default api
