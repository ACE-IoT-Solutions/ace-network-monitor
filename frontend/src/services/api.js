import axios from 'axios'

// Use environment variable if set, otherwise use empty string for same-origin (production)
// In development with vite dev server, you should set VITE_API_URL=http://localhost:8501
const API_BASE_URL = import.meta.env.VITE_API_URL || ''

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default {
  // System status
  async getStatus() {
    const response = await api.get('/api/status')
    return response.data
  },

  // Ping results
  async getLatestResults() {
    const response = await api.get('/api/ping-results/latest')
    return response.data
  },

  async getPingResults(hostAddress = null, hours = 24, limit = 1000) {
    const params = { hours, limit }
    if (hostAddress) params.host_address = hostAddress
    const response = await api.get('/api/ping-results', { params })
    return response.data
  },

  // Statistics
  async getHostStatistics(hostAddress, hours = 24) {
    const response = await api.get(`/api/statistics/${hostAddress}`, {
      params: { hours }
    })
    return response.data
  },

  // Outages
  async getOutageEvents(hostAddress = null, activeOnly = false, days = null, limit = 50) {
    const params = { active_only: activeOnly, limit }
    if (hostAddress) params.host_address = hostAddress
    if (days) params.days = days
    const response = await api.get('/api/outages', { params })
    return response.data
  },

  async getActiveOutages() {
    const response = await api.get('/api/outages/active')
    return response.data
  },

  async getOutageStatistics(hostAddress, days = null) {
    const params = days ? { days } : {}
    const response = await api.get(`/api/outages/statistics/${hostAddress}`, { params })
    return response.data
  },

  // Hosts
  async getHosts() {
    const response = await api.get('/api/hosts')
    return response.data
  },

  async getHostActiveOutage(hostAddress) {
    const response = await api.get(`/api/hosts/${hostAddress}/active-outage`)
    return response.data
  },

  // Health check
  async healthCheck() {
    const response = await api.get('/health')
    return response.data
  }
}
